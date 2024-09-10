# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import json
import re
from copy import deepcopy

import frappe
from datetime import datetime
from bs4 import BeautifulSoup, PageElement
from frappe.utils import cstr, strip_html_tags, update_progress_bar
from frappe.utils.synchronization import filelock
from redis.commands.search.field import TagField, TextField
from redis.commands.search.indexDefinition import IndexDefinition
from redis.commands.search.query import Query
from redis.exceptions import ResponseError

from helpdesk.utils import is_agent

STOPWORDS = [
    "a",
    "is",
    "the",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "if",
    "in",
    "into",
    "it",
    "no",
    "not",
    "of",
    "on",
    "or",
    "such",
    "that",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "was",
    "will",
    "with",
    "how",
    "what",
    "where",
    "when",
    "i",
    "you",
    "me",
    "do",
]


class Search:
    unsafe_chars = re.compile(r"[\[\]{}<>+]")

    def __init__(self, index_name, prefix, schema) -> None:
        self.redis = frappe.cache()
        self.index_name = index_name
        self.prefix = prefix
        self.schema = []
        for field in schema:
            self.schema.append(frappe._dict(field))

    def create_index(self):
        index_def = IndexDefinition(
            prefix=[f"{self.redis.make_key(self.prefix).decode()}:"],
        )
        schema = []
        for field in self.schema:
            kwargs = {
                k: v
                for k, v in field.items()
                if k in ["weight", "sortable", "no_index", "no_stem"]
            }
            if field.type == "tag":
                schema.append(TagField(field.name, **kwargs))
            else:
                schema.append(TextField(field.name, **kwargs))

        self.redis.ft(self.index_name).create_index(
            schema,
            definition=index_def,
            stopwords=STOPWORDS,
        )
        self._index_exists = True

    def add_document(self, id, doc):
        doc = frappe._dict(doc)
        doc_id = self.redis.make_key(f"{self.prefix}:{id}").decode()
        mapping = {}
        for field in self.schema:
            if field.name in doc:
                mapping[field.name] = cstr(doc[field.name])
        if self.index_exists():
            self.redis.ft(self.index_name).add_document(doc_id, replace=True, **mapping)

    def remove_document(self, id):
        key = self.redis.make_key(f"{self.prefix}:{id}").decode()
        if self.index_exists():
            self.redis.ft(self.index_name).delete_document(key)

    def search(
        self,
        query,
        start=0,
        page_length=5,
        highlight=False,
    ):
        query = self.clean_query(query)
        query = Query(query).paging(start, page_length)
        if highlight:
            query = query.highlight(tags=["<mark>", "</mark>"])

        query.summarize(fields=["description"])
        query.scorer("DISMAX")

        try:
            result = self.redis.ft(self.index_name).search(query)
        except ResponseError as e:
            print(e)
            return frappe._dict({"total": 0, "docs": [], "duration": 0})

        out = frappe._dict(docs=[], total=result.total, duration=result.duration)
        for doc in result.docs:
            id = doc.id.split(":", 1)[1]
            _doc = frappe._dict(doc.__dict__)
            _doc.id = id
            _doc.payload = json.loads(doc.payload) if doc.payload else None
            out.docs.append(_doc)
        return out

    def clean_query(self, query):
        query = query.strip().replace("-*", "*")
        query = self.unsafe_chars.sub(" ", query)
        query.strip()
        return query

    def spellcheck(self, query, **kwargs):
        return self.redis.ft(self.index_name).spellcheck(query, **kwargs)

    def drop_index(self):
        if self.index_exists():
            self.redis.ft(self.index_name).dropindex(delete_documents=True)

    def index_exists(self):
        self._index_exists = getattr(self, "_index_exists", None)
        if self._index_exists is None:
            try:
                self.redis.ft(self.index_name).info()
                self._index_exists = True
            except ResponseError:
                self._index_exists = False
        return self._index_exists


class HelpdeskSearch(Search):
    schema = [
        {"name": "name", "weight": 2},
        {"name": "subject", "weight": 6},
        {"name": "description", "weight": 6},
        {"name": "headings", "weight": 8},
        {"name": "team", "type": "tag"},
        {"name": "modified", "sortable": True},
        {"name": "creation", "sortable": True},
    ]

    DOCTYPE_FIELDS = {
        "HD Ticket": [
            "name",
            "subject",
            "description",
            "agent_group",
            "modified",
            "creation",
        ],
        "HD Article": [
            "name",
            "category",
            "title",
            "content",
            "modified",
            "creation",
            "category.category_name as category",
        ],
    }

    def __init__(self):
        super().__init__("helpdesk_idx", "search_doc", self.schema)

    def build_index(self):
        self.drop_index()
        self.create_index()
        records = self.get_records("HD Ticket") + self.get_records("HD Article")
        total = len(records)
        for i, doc in enumerate(records):
            self.index_doc(doc)
            if not hasattr(frappe.local, "request"):
                update_progress_bar("Indexing", i, total)

    def index_doc(self, doc):
        id = f"{doc.doctype}:{doc.name}"
        fields = None
        if doc.doctype == "HD Ticket":
            fields = {
                "doctype": doc.doctype,
                "name": doc.name,
                "subject": doc.subject,
                "team": doc.agent_group,
                "modified": doc.modified,
            }
        if doc.doctype == "HD Article":
            fields = {
                "doctype": doc.doctype,
                "name": doc.name,
                "subject": doc.title,
                "description": strip_html_tags(doc.content),
                "headings": doc.headings,
                "modified": doc.modified,
            }
        if fields:
            self.add_document(id, fields)

    def remove_doc(self, doc):
        key = f"{doc.doctype}:{doc.name}"
        self.remove_document(key)

    def extract_headings(self, content: str | None) -> str:
        try:
            soup = BeautifulSoup(content, "html.parser")
        except TypeError:
            ret = []
        else:
            ret = []
            for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                for heading in soup.find_all(tag):
                    ret.append(heading.text)
        return json.dumps(ret)

    def get_sections(self, content: str) -> list[tuple[str, str]]:
        try:
            soup = BeautifulSoup(content, "html.parser")
        except TypeError:
            return []
        else:
            sections = []
            tag: PageElement
            section = ""
            heading = ""
            for tag in soup.find_all():
                if tag.name in ["p", "blockquote", "code"]:
                    section += tag.text + "\n"
                elif tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    sections.append((heading, section))
                    section = ""
                    heading = tag.text
            sections.append((heading, section))
            return sections

    def scrub(self, text: str):
        # For permalink
        return re.sub(r"[^a-zA-Z0-9]+", "-", text).lower()

    def get_records(self, doctype):
        records = []
        for d in frappe.db.get_all(doctype, fields=self.DOCTYPE_FIELDS[doctype]):
            d.doctype = doctype
            if doctype == "HD Article":
                for heading, section in self.get_sections(d.content):
                    cd = deepcopy(d)
                    cd.name = d.name + f"#{self.scrub(heading)}"
                    cd.content = section
                    cd.headings = heading
                    records.append(cd)
            elif doctype == "HD Ticket":
                d.headings = self.extract_headings(d.description)
                records.append(d)
        return records


@frappe.whitelist()
def search(query, only_articles=False):
    search = HelpdeskSearch()
    query = search.clean_query(query)
    query_parts = query.split(" ")
    query = " ".join(
        [f"%{q}%" for q in query_parts if q not in STOPWORDS]
    )  # for stopwords to be ignored
    result = search.search(query, start=0, highlight=True)
    groups = {}
    for r in result.docs:
        doctype, name = r.id.split(":")
        r.doctype = doctype
        r.name = name
        if doctype == "HD Ticket" and not only_articles:
            if not is_agent():
                r = []
            groups.setdefault("Tickets", []).append(r)
        if doctype == "HD Article":
            groups.setdefault("Articles", []).append(r)

    out = []
    for key in groups:
        out.append({"title": key, "items": groups[key]})
    return out


@filelock("helpdesk_search_indexing", timeout=60)
def build_index():
    frappe.cache().set_value("helpdesk_search_indexing_in_progress", True)
    search = HelpdeskSearch()
    search.build_index()
    frappe.cache().set_value("helpdesk_search_indexing_in_progress", False)


def build_index_in_background():
    if not frappe.cache().get_value("helpdesk_search_indexing_in_progress"):
        frappe.enqueue(build_index, queue="long")


def build_index_if_not_exists():
    search = HelpdeskSearch()
    if not search.index_exists():
        build_index()


@filelock("helpdesk_corpus_download", timeout=60)
def download_corpus():
    from nltk import data, download

    try:
        data.find("taggers/averaged_perceptron_tagger_eng.zip")
        data.find("tokenizers/punkt_tab.zip")
    except LookupError:
        download("averaged_perceptron_tagger_eng")
        download("punkt_tab")

@frappe.whitelist()
def handle_send_mail_track_sla():
    if frappe.db.get_value("HD Settings", None, "track_service_level_agreement") :
        if 'Agent' in frappe.get_roles() :
            
            # lấy thông tin ngôn ngữ mà user đang sử dụng
            
            user_email = frappe.session.user
            user = frappe.get_doc("User", user_email)
            if user :
                language = user.language if user.language else 'en'
            else :
                language = 'en'
            
            
            # Lấy dữ liệu hai cột thiết lập thời gian gửi thông báo trong doctype Hd Setting
            
            time_setting_send_email = frappe.db.get_value("HD Settings", None, "time_setting_send_email")
            select_type_time_send_email = frappe.db.get_value("HD Settings", None, "select_type_time_send_email")


            # Xác định đơn vị thời gian
            
            if select_type_time_send_email == 'minutes':
                time_unit = 'MINUTE'
            elif select_type_time_send_email == 'hours':
                time_unit = 'HOUR'
            else :
                time_unit = 'DAY'

                
            # Sql lấy dữ liệu theo thông tin người dùng nhập vào hai trường thời gian và loại thời gian trong doctype HD Setting
            
            query = f""" SELECT name FROM `tabHD Ticket` WHERE TIMESTAMPDIFF({time_unit}, NOW(), `resolution_by`) = %s """
            tickets = frappe.db.sql(query, (time_setting_send_email,), as_dict=True)
            
            
            # Check ngôn ngữ mà user đăng nhập đang dùng để  trả về thông báo cho hợp lý
            if language == 'vi':
                list_notifications = []
                for item in tickets :
                    ticket_id = item.get('name')
                    list_notifications.append({'name': f"Phiếu {ticket_id} sắp đến hạn SLA"})
                return list_notifications
            else :
                list_notifications = []
                for item in tickets :
                    ticket_id = item.get('name')
                    list_notifications.append({'name': f"Ticket {{ {ticket_id} }} is reaching its SLA deadline"})
                return list_notifications
            
@frappe.whitelist()
def handle_send_mail_allow_resetting_sla():
    if frappe.db.get_value("HD Settings", None, "allow_resetting_service_level_agreement") :
        if 'Agent' in frappe.get_roles() :

            current_user = frappe.session.user
            user_info = frappe.db.get_value("User", current_user, ["full_name"])
            
            # Lấy ngôn ngữ của người dùng
            user = frappe.get_doc("User", current_user)
            language = user.language if user.language else 'en'
        
            get_list_ticket = frappe.get_all(
                "HD Ticket",
                fields=["name", "subject", "response_by", "resolution_by","_assign"],  
            )
            
            for ticket in get_list_ticket :

                if ticket.get('_assign') :
                    convert_list_assign = json.loads(ticket.get('_assign'))
                    for list_email in convert_list_assign :

                        get_full_name = frappe.db.get_value("User", {"email": list_email }, "full_name")

                        if language == 'vi':
                            subject = "Nhắc nhở: Các phiếu hỗ trợ gần đến hạn SLA cần được xử lý"
                            greeting = f"Kính gửi {get_full_name},"
                            intro = f"Chúng tôi xin thông báo rằng hiện đang có 1 phiếu đang gần đến hạn SLA cần được xử lý. Để đảm bảo chất lượng dịch vụ và đáp ứng yêu cầu của khách hàng đúng hạn, vui lòng xem lại và xử lý các phiếu này ngay lập tức."
                        else:  # Ngôn ngữ khác, mặc định là tiếng Anh
                            subject = "Reminder: SLA Approaching Tickets Need Immediate Attention"
                            greeting = f"Dear {get_full_name},"
                            intro = f"We would like to inform you that there are currently 1 support tickets nearing their SLA deadlines and require immediate attention. To ensure service quality and meet customer expectations on time, please review and address these tickets as soon as possible."
                        convert_time_response_by = handle_convert_datetime_to_date(str(ticket['response_by']))
                        convert_time_resolution_by = handle_convert_datetime_to_date(str(ticket['resolution_by']))
                        # Tạo nội dung bảng HTML
                        table_rows = "".join(
                            f"<tr><td>{ticket['name']}</td><td>{ticket['subject']}</td><td style='text-align:center'>{convert_time_response_by}</td><td style='text-align:center'>{convert_time_resolution_by}</td></tr>"
                        )
                        if language == 'vi':
                            table = f"""
                                <table border="1" cellpadding="5" style="width: 100%;">
                                    <tr>
                                        <th>ID</th>
                                        <th>Tiêu đề</th>
                                        <th>Trạng thái phản hồi</th>
                                        <th>Trạng thái xử lý</th>
                                    </tr>
                                </table>
                            """
                        else :
                            table = f"""
                                <table border="1" cellpadding="5" style="width: 100%;">
                                    <tr>
                                        <th>Ticket ID</th>
                                        <th>Subject</th>
                                        <th>First Response</th>
                                        <th>Resolution</th>
                                    </tr>
                                    {table_rows}
                                </table>
                            """
                        message = f"""
                            {greeting}<br><br>
                            {intro}<br><br>
                            {table}
                        """
                        # Gửi email
                        frappe.sendmail(
                            recipients=[list_email],
                            subject=subject,
                            message=message,
                            send_after=0  # 0 để gửi ngay lập tức, có thể thiết lập thời gian nếu cần
                        )
                        
def handle_convert_datetime_to_date(time) :
    response_by_datetime = datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
    return response_by_datetime.date()


def create_dynamic_scheduler_events():
    # SQL query lấy workday và start_time
    query = """
        SELECT 
            sd.workday,
            sd.start_time
        FROM `tabHD Service Level Agreement` as sla
        RIGHT JOIN `tabHD Service Day` as sd on sd.parent = sla.name
        WHERE sla.name = 'Default';
    """

    # Thực thi SQL query để lấy workday và start_time
    result = frappe.db.sql(query, as_dict=True)

    # Mapping workday sang cron format (mapping các ngày sang số tương ứng trong cron)
    day_to_cron = {
        "Monday": 1,
        "Tuesday": 2,
        "Wednesday": 3,
        "Thursday": 4,
        "Friday": 5,
        "Saturday": 6,
        "Sunday": 0
    }

    # Tạo cron expressions
    scheduler_events = {
        "cron": {}
    }

    for row in result:
        workday = row["workday"]
        start_time = row["start_time"]

        # Chuyển đổi start_time sang hour và minute
        hour, minute, _ = str(start_time).split(":")
        
        # Tạo cron string cho workday và start_time
        cron_string = f"{minute} {hour} * * {day_to_cron[workday]}"
        
        # Thêm vào scheduler_events với hàm cần chạy
        scheduler_events["cron"][cron_string] = ["helpdesk.search.handle_send_mail_track_sla"]

    return scheduler_events

