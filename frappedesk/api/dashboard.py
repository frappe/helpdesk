import frappe
import datetime

@frappe.whitelist()
def get_ticket_count(filters=None):
    ticket_count = frappe.db.get_list('Ticket',filters=filters,fields=['count(name) as count','creation'],group_by='creation',order_by='creation asc')

    return ticket_count

@frappe.whitelist()
def ticket_summary(startDate=None,endDate=None):
    print(startDate)
    if startDate and endDate:
        startDate= datetime.datetime.strptime(startDate, "%Y-%m-%d").strftime("%d-%m")
        endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d").strftime("%d-%m")
    ticket_count = frappe.db.sql("""select TO_CHAR(creation,'DD/MM') as date,
                                COUNT(Case when status="Open" then status end) as "Open", 
                                COUNT(Case when status="Closed" then status end) as "Closed", 
                                COUNT(Case when status="Replied" then status end) as "Replied" 
                                from `tabTicket` WHERE TO_CHAR(creation,'DD/MM') BETWEEN %s AND %s group by 
                                TO_CHAR(creation,'DD/MM')
                                ORDER BY TO_CHAR(creation,'MM/DD') ASC""",(startDate,endDate))
    print(ticket_count)
    return ticket_count

@frappe.whitelist()
def ticket_status():
    ticket_count_by_status = frappe.db.get_list('Ticket',fields=['count(name) as count','status','creation','resolution_by'],group_by='status')
    
    return ticket_count_by_status

@frappe.whitelist()
def ticket_type(filters=None):                                                                                                      
    ticket_count_by_type= frappe.db.get_list('Ticket',filters=filters, fields=['count(name) as count','ticket_type'],group_by='ticket_type')

    return ticket_count_by_type

@frappe.whitelist()
def average_first_response_time():
    average_response_time = float(0.0)
    ticket_list = frappe.get_list('Ticket', fields=['name','first_response_time'],filters={'first_response_time':['not like','']})

    for ticket in ticket_list:
        average_response_time +=ticket.first_response_time

    return round((((average_response_time)/len(ticket_list))/3600),1)

@frappe.whitelist()
def average_resolution_time():
    average_resolution_time = float(0.0)
    ticket_list = frappe.get_list('Ticket', fields=['name','resolution_time'],filters={'resolution_time':['not like','']})

    for ticket in ticket_list:
        average_resolution_time += ticket.resolution_time

    return round((((average_resolution_time)/len(ticket_list))/3600),1)

@frappe.whitelist()
def resolution_within_sla():
    ticket_list = frappe.get_list('Ticket', filters={'status':'Closed'}, fields=['name','agreement_status','sla'])
    count = 0

    for ticket in ticket_list:
        if ticket.agreement_status == 'Fulfilled':
            count = count + 1

    resolution_within_sla_percentage = (count/len(ticket_list))*100
    resolution_within_sla_percentage = round(resolution_within_sla_percentage,1)

    return str(resolution_within_sla_percentage) + "%"

@frappe.whitelist()
def feedback_status(dateFilter=None):
    feedback_status_count = frappe.db.get_list('Ticket',filters=[{'feedback_status':['not like','']},dateFilter],fields=['count(name) as value', 'feedback_status as name'],group_by='feedback_status')

    return feedback_status_count