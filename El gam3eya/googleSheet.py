import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

SHEET_URL = "https://docs.google.com/spreadsheets/d/1kPMHl4JpCATOxv9XXbLM7BcRUMyNMbe3eMUjijuXWLg/edit?usp=sharing"

def get_gsheet_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("gam3eya-465809-2adc07257629.json", scope)
    client = gspread.authorize(creds)
    return client

def get_due_customers():
    client = get_gsheet_client()
    sheet = client.open_by_url(SHEET_URL).sheet1 
    records = sheet.get_all_records()  

    today = datetime.today().date()
    due_customers = []

    for i, row in enumerate(records):
        try:
            due_date_str = str(row['due_date']).strip()
            if due_date_str:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            else:
                print(f"Skipping row {i+2} - Invalid or empty due_date")
                continue  
            
            amount_due = row.get('amount_due', 'غير معروف')  
            payment_status = row['paying_status'].strip().lower()
            contact_status = str(row.get('contact_status', '')).strip().lower()

            if contact_status == "contacted":
                print(f"Skipping customer {row['name']} - Already contacted.")
                continue

            if due_date <= today and payment_status != "paid" and contact_status != "contacted":
                row['row_index'] = i + 2  
                row['amount_due'] = amount_due  
                due_customers.append(row)
        except Exception as e:
            print(f"Error processing row {i+2}: {e}")

    if not due_customers:
        print("✅ No customers to contact - all overdue customers have been contacted.")
    
    return due_customers


def mark_customer_contacted(row_index, feedback="تم التواصل"):
    client = get_gsheet_client()
    sheet = client.open_by_url(SHEET_URL).sheet1
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        sheet.update(f"I{row_index}", [["contacted"]]) 
        sheet.update(f"G{row_index}", [[now]]) 
        sheet.update(f"H{row_index}", [[feedback]])

        print(f"✅ Marked customer at row {row_index} as contacted at {now}")
    except Exception as e:
        print(f"Error marking customer at row {row_index} as contacted: {e}")
