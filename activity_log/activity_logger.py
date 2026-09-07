import os
import csv
from datetime import datetime
from config import DATA_DIR

BUYERS_CSV = os.path.join(DATA_DIR, 'buyers.csv')
SENT_LOG_CSV = os.path.join(DATA_DIR, 'sent_log.csv')
BUSINESS_CSV = os.path.join(DATA_DIR, 'business_emails.csv')
INDIVIDUAL_CSV = os.path.join(DATA_DIR, 'individual_emails.csv')
OPTED_OUT_CSV = os.path.join(DATA_DIR, 'opted_out.csv')

def init_csv_files():
    """Create CSV files with correct headers if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    files_headers = {
        BUYERS_CSV: ["buyer_name", "company_name", "email", "website", "country", "source_platform", "source_url", "discovered_date"],
        SENT_LOG_CSV: ["email_address", "campaign_name", "status", "timestamp"],
        BUSINESS_CSV: ["email_address", "classified_date"],
        INDIVIDUAL_CSV: ["email_address", "classified_date"],
        OPTED_OUT_CSV: ["email_address", "opt_out_date"]
    }
    
    for file_path, headers in files_headers.items():
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
            except Exception as e:
                print(f"Error creating file {file_path}: {e}")

# Initialize files on import
init_csv_files()

def get_all_buyers():
    """Read all records from buyers.csv."""
    init_csv_files()
    records = []
    if not os.path.exists(BUYERS_CSV):
        return records
    try:
        with open(BUYERS_CSV, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    except Exception as e:
        print(f"Error reading buyers.csv: {e}")
    return records

def write_buyers(records):
    """Write list of records (dicts) to buyers.csv, preventing duplicates by email."""
    init_csv_files()
    existing_buyers = get_all_buyers()
    existing_emails = {b['email'].strip().lower() for b in existing_buyers if b.get('email')}
    
    new_count = 0
    try:
        with open(BUYERS_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for r in records:
                email = r.get('email', '').strip().lower()
                if email and email not in existing_emails:
                    writer.writerow([
                        r.get("buyer_name", ""),
                        r.get("company_name", ""),
                        r.get("email", ""),
                        r.get("website", ""),
                        r.get("country", ""),
                        r.get("source_platform", ""),
                        r.get("source_url", ""),
                        r.get("discovered_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    ])
                    existing_emails.add(email)
                    new_count += 1
    except Exception as e:
        print(f"Error writing to buyers.csv: {e}")
    return new_count

def get_opted_out_emails():
    """Get a set of lowercase email addresses that have opted out."""
    init_csv_files()
    opted_out = set()
    if not os.path.exists(OPTED_OUT_CSV):
        return opted_out
    try:
        with open(OPTED_OUT_CSV, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('email_address'):
                    opted_out.add(row['email_address'].strip().lower())
    except Exception as e:
        print(f"Error reading opted_out.csv: {e}")
    return opted_out

def add_opt_out(email):
    """Add email address to opted_out.csv if not already present."""
    init_csv_files()
    email = email.strip().lower()
    if not email:
        return False
        
    opted_out = get_opted_out_emails()
    if email in opted_out:
        return False
        
    try:
        with open(OPTED_OUT_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        return True
    except Exception as e:
        print(f"Error writing to opted_out.csv: {e}")
        return False

def remove_opt_out(email):
    """Remove email address from opted_out.csv."""
    init_csv_files()
    email = email.strip().lower()
    if not email:
        return False
    
    rows = []
    removed = False
    try:
        with open(OPTED_OUT_CSV, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            for row in reader:
                if row and row[0].strip().lower() == email:
                    removed = True
                else:
                    rows.append(row)
        
        if removed:
            with open(OPTED_OUT_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        return removed
    except Exception as e:
        print(f"Error removing from opted_out.csv: {e}")
        return False

def log_send_attempt(email, campaign_name, status):
    """Append send log entry."""
    init_csv_files()
    try:
        with open(SENT_LOG_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                email,
                campaign_name,
                status,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
    except Exception as e:
        print(f"Error logging send attempt: {e}")

def get_sent_logs():
    """Read all send attempts."""
    init_csv_files()
    logs = []
    if not os.path.exists(SENT_LOG_CSV):
        return logs
    try:
        with open(SENT_LOG_CSV, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
    except Exception as e:
        print(f"Error reading sent_log.csv: {e}")
    return logs

def get_classified_emails():
    """Get classified business and individual emails as sets."""
    init_csv_files()
    business = set()
    individual = set()
    
    if os.path.exists(BUSINESS_CSV):
        try:
            with open(BUSINESS_CSV, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('email_address'):
                        business.add(row['email_address'].strip().lower())
        except Exception as e:
            print(f"Error reading business_emails.csv: {e}")
            
    if os.path.exists(INDIVIDUAL_CSV):
        try:
            with open(INDIVIDUAL_CSV, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('email_address'):
                        individual.add(row['email_address'].strip().lower())
        except Exception as e:
            print(f"Error reading individual_emails.csv: {e}")
            
    return business, individual

def write_classified_emails(business_list, individual_list):
    """Write list of classified business and individual emails, avoiding duplicates."""
    init_csv_files()
    existing_biz, existing_ind = get_classified_emails()
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        if business_list:
            with open(BUSINESS_CSV, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for email in business_list:
                    email_clean = email.strip().lower()
                    if email_clean and email_clean not in existing_biz:
                        writer.writerow([email_clean, now_str])
                        existing_biz.add(email_clean)
        
        if individual_list:
            with open(INDIVIDUAL_CSV, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for email in individual_list:
                    email_clean = email.strip().lower()
                    if email_clean and email_clean not in existing_ind:
                        writer.writerow([email_clean, now_str])
                        existing_ind.add(email_clean)
    except Exception as e:
        print(f"Error writing classified emails: {e}")

def clear_database():
    """Clear all data files except opted_out.csv."""
    files_headers = {
        BUYERS_CSV: ["buyer_name", "company_name", "email", "website", "country", "source_platform", "source_url", "discovered_date"],
        SENT_LOG_CSV: ["email_address", "campaign_name", "status", "timestamp"],
        BUSINESS_CSV: ["email_address", "classified_date"],
        INDIVIDUAL_CSV: ["email_address", "classified_date"]
    }
    
    for file_path, headers in files_headers.items():
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        except Exception as e:
            print(f"Error clearing file {file_path}: {e}")
