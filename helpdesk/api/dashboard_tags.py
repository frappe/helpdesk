"""Tag charts for the dashboard.

1. Top Tags   - what is being tagged most (volume)
2. Tag Trend  - when tags spike (emerging issues)

Tags live in `Tag Link`, not in a scalar column, so these cannot reuse the
group-by helpers the other master charts use.
"""

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Function
from pypika import Order

from helpdesk.api.dashboard import HD_TICKET, HelpdeskDashboard, get_bar_chart_config

TOP_TAG_COUNT = 10
TREND_TAG_COUNT = 5


class TagDashboard(HelpdeskDashboard):
    """Tag charts, reusing the dashboard's date / team / agent conditions."""

    def __init__(self, filters):
        super().__init__(filters)
        self.tag_link = DocType("Tag Link")

    def get_tag_chart_data(self) -> list[dict[str, any]]:
        return [
            self.get_top_tags_chart(),
            self.get_tag_trend_chart(),
        ]

    def get_top_tags_chart(self) -> dict[str, any]:
        """Horizontal bars: the label is the value here, so give it the long axis."""
        tickets = "Tickets"
        top_tag_data = self.get_tag_counts(TOP_TAG_COUNT)
        for tag_row in top_tag_data:
            tag_row[tickets] = tag_row.pop("count")

        return get_bar_chart_config(
            # bars are drawn bottom-up, so ascending puts the biggest on top
            top_tag_data[::-1],
            "top_tags",
            _("Top Tags"),
            _("Most used tags in this period"),
            {"key": "tag", "type": "category", "title": _("Tag")},
            _("Tickets"),
            [{"name": tickets, "type": "bar", "showDataLabels": True}],
            swapXY=True,
        )

    def get_tag_trend_chart(self) -> dict[str, any]:
        """Daily stack of the busiest tags, so a spike in one is visible."""
        tags = [tag_row.tag for tag_row in self.get_tag_counts(TREND_TAG_COUNT)]
        date = Function("DATE", self.ticket.creation)
        rows = (
            self.get_tagged_tickets()
            .select(
                date.as_("date"),
                self.tag_link.tag,
                Count(self.ticket.name).as_("count"),
            )
            .where(self.tag_link.tag.isin(tags or [""]))
            .groupby(date, self.tag_link.tag)
        ).run(as_dict=True)

        return get_bar_chart_config(
            self.pivot_by_date(rows, tags),
            "tag_trend",
            _("Tag Trend"),
            _("Daily volume of the top {0} tags").format(TREND_TAG_COUNT),
            {"key": "date", "type": "time", "title": _("Date"), "timeGrain": "day"},
            _("Tickets"),
            [{"name": tag, "type": "bar", "stackName": "tags"} for tag in tags],
            stacked=True,
        )

    def get_tag_counts(self, limit: int | None = None) -> list[dict[str, any]]:
        """Ticket count per tag, busiest first.
        Top 10 tags for the duration of the dashboard's date filter.
        """

        count = Count(self.ticket.name)
        query = (
            self.get_tagged_tickets()
            .select(self.tag_link.tag, count.as_("count"))
            .groupby(self.tag_link.tag)
            .orderby(count, order=Order.desc)
        )
        if limit:
            query = query.limit(limit)
        return query.run(as_dict=True)

    def get_tagged_tickets(self):
        """`Tag Link` joined to the tickets this dashboard is scoped to."""
        query = (
            frappe.qb.from_(self.tag_link)
            .inner_join(self.ticket)
            .on(self.tag_link.document_name == self.ticket.name)
            .where(self.tag_link.document_type == HD_TICKET)
            .where(self.ticket.creation >= self.from_date)
            .where(self.ticket.creation < self.to_date_next)
        )
        return query.where(self.combined_cond) if self.combined_cond else query

    @staticmethod
    def pivot_by_date(
        rows: list[dict[str, any]], tags: list[str]
    ) -> list[dict[str, any]]:
        """One row per date with a column per tag, zero filled so bars stack."""
        by_date = {}
        for row in rows:
            day = by_date.setdefault(row.date, dict.fromkeys(tags, 0))
            day["date"] = row.date
            day[row.tag] = row.count
        return [by_date[date] for date in sorted(by_date)]
