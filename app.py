import os
import sys
import csv
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename

# Ensure standard output can print Unicode characters on Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import custom pipeline modules
from config import config, DATA_DIR
from activity_log.activity_logger import (
    get_all_buyers,
    get_opted_out_emails,
    add_opt_out,
    remove_opt_out,
    get_classified_emails,
    write_buyers,
    clear_database,
    OPTED_OUT_CSV,
    get_sent_logs
)
from search import search_google, search_facebook, search_linkedin, search_directory
from extraction import extract_and_normalize
from validation import is_valid_email
from outreach import (
    run_ai_classification,
    run_outreach_campaign,
    send_single_email,
    is_oauth_configured,
    is_smtp_configured,
    test_smtp_connection,
    get_auth_mode
)
from reports import get_campaign_statistics, get_last_run_statistics

app = Flask(__name__)
# Standard secret key for session flash messages
app.secret_key = os.getenv("FLASK_SECRET_KEY", "singing-bowls-export-secret-key-2026")

UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure secure headers on all responses
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response

def datetime_from_timestamp(ts):
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

# ==========================================
# WEB DASHBOARD ROUTES
# ==========================================

@app.route('/')
def index():
    buyers = get_all_buyers()
    biz_emails, ind_emails = get_classified_emails()
    opted_out = get_opted_out_emails()
    
    return render_template(
        'index.html',
        active_page='index',
        buyer_count=len(buyers),
        biz_count=len(biz_emails),
        ind_count=len(ind_emails),
        opt_count=len(opted_out),
        search_keyword=config.get("SEARCH_KEYWORD"),
        gmail_email=config.get("GMAIL_EMAIL"),
        daily_limit=config.get("DAILY_SEND_LIMIT"),
        has_gemini_key=bool(config.get("GEMINI_API_KEY")),
        auth_mode=get_auth_mode(),
        smtp_configured=is_smtp_configured(),
        oauth_configured=is_oauth_configured(),
        recent_buyers=buyers[-15:]  # Show last 15 discovered buyers
    )

@app.route('/run-discovery', methods=['GET', 'POST'])
def run_discovery():
    if request.method == 'POST':
        keyword = request.form.get("keyword", config.get("SEARCH_KEYWORD") or "Singing Bowls").strip()
        max_results = int(request.form.get("max_results", "5"))
    else:
        keyword = request.args.get("keyword", config.get("SEARCH_KEYWORD") or "Singing Bowls").strip()
        max_results = int(request.args.get("max_results", "5"))
    
    config.update({"SEARCH_KEYWORD": keyword})
    
    # 1. Run Search Adapters
    google_leads = search_google(keyword, max_results)
    facebook_leads = search_facebook(keyword, max_results)
    linkedin_leads = search_linkedin(keyword, max_results)
    directory_leads = search_directory(keyword, max_results)
    
    # 2. Aggregate raw leads
    aggregated_raw = google_leads + facebook_leads + linkedin_leads + directory_leads
    
    # 3. Extract and Normalize
    normalized_records = []
    for item in aggregated_raw:
        try:
            record = extract_and_normalize(item)
            if record.get('email') and is_valid_email(record.get('email')):
                normalized_records.append(record)
        except Exception as e:
            print(f"[Flask Server] Error processing raw search item: {e}")
            
    # 4. Write to buyers database
    new_leads_added = write_buyers(normalized_records)
    
    if new_leads_added > 0:
        flash(f"Discovery complete! Sourced {len(aggregated_raw)} listings across sources. Added {new_leads_added} new verified leads to database.", "success")
    else:
        flash(f"Discovery complete! Found {len(aggregated_raw)} listings, but these leads already exist in your database (duplicates skipped). Check the leads table below or search a new keyword!", "info")
    return redirect(url_for('index'))

@app.route('/reset-leads', methods=['POST'])
def reset_leads():
    clear_database()
    flash("Leads database cleared. You can now run a fresh discovery pipeline!", "info")
    return redirect(url_for('index'))

@app.route('/upload')
def upload():
    opt_outs = []
    if os.path.exists(OPTED_OUT_CSV):
        try:
            with open(OPTED_OUT_CSV, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    opt_outs.append(row)
        except Exception as e:
            print(f"[Flask Server] Error reading opted_out.csv: {e}")
            
    buyers_csv_path = os.path.join(DATA_DIR, 'buyers.csv')
    
    db_stats = {
        "row_count": len(get_all_buyers()),
        "file_size_kb": round(os.path.getsize(buyers_csv_path) / 1024, 2) if os.path.exists(buyers_csv_path) else 0,
        "last_modified": datetime_from_timestamp(os.path.getmtime(buyers_csv_path)) if os.path.exists(buyers_csv_path) else "n/a"
    }
    
    return render_template(
        'upload.html',
        active_page='upload',
        db_stats=db_stats,
        opt_outs=opt_outs
    )

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    if 'csv_file' not in request.files:
        flash("No file part in the upload request.", "error")
        return redirect(url_for('upload'))
        
    file = request.files['csv_file']
    if file.filename == '':
        flash("No file selected.", "error")
        return redirect(url_for('upload'))
        
    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        imported_records = []
        try:
            with open(temp_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                required_headers = ['email']
                headers = reader.fieldnames if reader.fieldnames else []
                if not any(h in headers for h in required_headers):
                    flash("Invalid CSV format. Header 'email' is required at minimum.", "error")
                    return redirect(url_for('upload'))
                
                for row in reader:
                    email = row.get('email', '').strip()
                    if email and is_valid_email(email):
                        imported_records.append({
                            "buyer_name": row.get('buyer_name', row.get('name', 'Purchasing Manager')),
                            "company_name": row.get('company_name', row.get('company', 'Unknown Company')),
                            "email": email,
                            "website": row.get('website', ''),
                            "country": row.get('country', 'United States'),
                            "source_platform": row.get('source_platform', 'Manual Upload'),
                            "source_url": row.get('source_url', ''),
                            "discovered_date": row.get('discovered_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        })
            
            new_added = write_buyers(imported_records)
            flash(f"Import successful! Loaded {len(imported_records)} records, added {new_added} new verified entries.", "success")
        except Exception as e:
            flash(f"Error parsing uploaded CSV: {e}", "error")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    else:
        flash("Unsupported file format. Please upload a valid CSV file.", "error")
        
    return redirect(url_for('upload'))

@app.route('/add-optout', methods=['POST'])
def add_optout():
    email = request.form.get("email", "").strip()
    if email:
        added = add_opt_out(email)
        if added:
            flash(f"Successfully unsubscribed {email}.", "success")
        else:
            flash(f"{email} is already in the unsubscribe list.", "info")
    return redirect(url_for('upload'))

@app.route('/remove-optout', methods=['POST'])
def remove_optout_route():
    email = request.form.get("email", "").strip()
    if email:
        removed = remove_opt_out(email)
        if removed:
            flash(f"Removed {email} from unsubscribe list.", "success")
        else:
            flash(f"Could not locate {email} in unsubscribe list.", "error")
    return redirect(url_for('upload'))

@app.route('/clear-db', methods=['POST'])
def clear_db():
    clear_database()
    flash("Database reset complete. Discovered buyers, classification lists, and campaigns have been cleared.", "success")
    return redirect(url_for('upload'))

@app.route('/classify')
def classify():
    biz, ind = get_classified_emails()
    return render_template(
        'classify.html',
        active_page='classify',
        biz_emails=sorted(list(biz)),
        ind_emails=sorted(list(ind))
    )

@app.route('/run-classify', methods=['POST'])
def run_classify():
    biz_added, ind_added = run_ai_classification(batch_size=10)
    flash(f"AI Classification complete! Added {biz_added} corporate accounts to Business store, and {ind_added} personal accounts to Individual store.", "success")
    return redirect(url_for('classify'))

@app.route('/send')
def send():
    buyers = get_all_buyers()
    biz, ind = get_classified_emails()
    
    return render_template(
        'send.html',
        active_page='send',
        buyer_count=len(buyers),
        biz_count=len(biz),
        ind_count=len(ind),
        default_subject=config.get("DEFAULT_SUBJECT"),
        default_body=config.get("DEFAULT_BODY"),
        send_delay=config.get("SEND_DELAY"),
        daily_limit=config.get("DAILY_SEND_LIMIT"),
        physical_address=config.get("PHYSICAL_ADDRESS"),
        gmail_email=config.get("GMAIL_EMAIL"),
        attachment_present=os.path.exists(os.path.join(config.BASE_DIR, 'assets', 'company_presentation.pdf')),
        auth_mode=get_auth_mode(),
        smtp_configured=is_smtp_configured(),
        oauth_configured=is_oauth_configured()
    )

@app.route('/run-send', methods=['POST'])
def run_send():
    subject = request.form.get("subject", "").strip()
    body = request.form.get("body", "").strip()
    audience = request.form.get("audience", "business")
    
    attachment_path = os.path.join(config.BASE_DIR, 'assets', 'company_presentation.pdf')
    
    # Check if a custom PDF was uploaded in this request
    if 'pdf_file' in request.files:
        pdf_file = request.files['pdf_file']
        if pdf_file and pdf_file.filename.endswith('.pdf'):
            try:
                pdf_file.save(attachment_path)
                print(f"[Flask Server] Saved new custom presentation PDF to: {attachment_path}")
            except Exception as e:
                print(f"[Flask Server] Error saving uploaded PDF: {e}")
                flash(f"Warning: Failed to save uploaded PDF ({e}). Using existing default.", "warning")
    
    # Run outreach campaign
    result = run_outreach_campaign(
        subject_template=subject,
        body_template=body,
        audience=audience,
        attachment_path=attachment_path
    )
    
    if "error" in result:
        flash(f"Campaign execution halted: {result['error']}", "error")
        return redirect(url_for('send'))
        
    flash(f"Campaign complete! Mode: {result.get('auth_mode', 'standard').upper()}. Dispatched {result['success_count']} emails successfully, {result['failed_count']} failed.", "success")
    return redirect(url_for('report'))

@app.route('/quick-test-send', methods=['POST'])
def quick_test_send():
    """Allows sending an immediate test email to the user's email address for screenshots."""
    recipient = request.form.get("test_recipient", config.get("GMAIL_EMAIL")).strip()
    if not recipient:
        flash("Please specify a valid recipient email address.", "error")
        return redirect(url_for('send'))
        
    subject = request.form.get("test_subject", "Singing Bowls Export Outreach — Sample Offer").strip()
    body = request.form.get("test_body", (
        "Dear Purchasing Partner,\n\n"
        "We are pleased to introduce our handcrafted Tibetan & Himalayan Singing Bowls direct export catalog.\n\n"
        "Attached is our comprehensive product line and wholesale specifications.\n\n"
        "Best regards,\n"
        "Export Operations Team"
    )).strip()
    
    attachment_path = os.path.join(config.BASE_DIR, 'assets', 'company_presentation.pdf')
    ok, message, status = send_single_email(recipient, subject, body, attachment_path)
    
    if ok:
        flash(f"Success! Test email delivered to {recipient} (Status: {status.upper()}). You can view it in your Gmail Inbox/Sent items for your screenshot!", "success")
    else:
        flash(f"Send failed: {message}", "error")
        
    return redirect(url_for('send'))

@app.route('/report')
def report():
    global_stats = get_campaign_statistics()
    last_run = get_last_run_statistics()
    sent_logs = get_sent_logs()[-25:]  # Last 25 send events
    
    return render_template(
        'report.html',
        active_page='report',
        global_stats=global_stats,
        last_run=last_run,
        sent_logs=reversed(sent_logs)
    )

@app.route('/download-report')
def download_report():
    sent_log_path = os.path.join(DATA_DIR, 'sent_log.csv')
    if os.path.exists(sent_log_path):
        return send_file(
            sent_log_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"campaign_outbox_report_{datetime.now().strftime('%Y%m%d')}.csv"
        )
    else:
        flash("Outbox report is empty. Please run a campaign first.", "error")
        return redirect(url_for('report'))

@app.route('/settings')
def settings():
    return render_template(
        'settings.html',
        active_page='settings',
        settings=config.settings,
        smtp_configured=is_smtp_configured(),
        auth_mode=get_auth_mode()
    )

@app.route('/save-settings', methods=['POST'])
def save_settings():
    new_settings = {}
    for key in config.settings.keys():
        if key in request.form:
            new_settings[key] = request.form.get(key)
            
    config.update(new_settings)
    flash("Pipeline configurations updated and saved successfully.", "success")
    return redirect(url_for('settings'))

@app.route('/test-smtp', methods=['POST'])
def test_smtp_route():
    email = request.form.get("email", config.get("GMAIL_EMAIL")).strip()
    password = request.form.get("password", config.get("GMAIL_APP_PASSWORD")).strip()
    
    ok, msg = test_smtp_connection(email, password)
    if ok:
        flash(f"SMTP Connection Successful: {msg}", "success")
    else:
        flash(f"SMTP Connection Failed: {msg}", "error")
        
    return redirect(url_for('settings'))

# ==========================================
# REST API ENDPOINTS (API EXPORT)
# ==========================================

@app.route('/api/buyers', methods=['GET'])
def api_get_buyers():
    """
    GET /api/buyers
    Optional Query Params:
      - keyword: filter by company name, buyer name, or email
      - country: filter by country
      - platform: filter by source platform
      - limit: max records to return (default 50)
      - offset: pagination offset (default 0)
    """
    buyers = get_all_buyers()
    keyword = request.args.get('keyword', '').strip().lower()
    country = request.args.get('country', '').strip().lower()
    platform = request.args.get('platform', '').strip().lower()
    
    filtered = buyers
    if keyword:
        filtered = [b for b in filtered if keyword in b.get('company_name', '').lower() 
                    or keyword in b.get('buyer_name', '').lower() 
                    or keyword in b.get('email', '').lower()]
    if country:
        filtered = [b for b in filtered if country in b.get('country', '').lower()]
    if platform:
        filtered = [b for b in filtered if platform in b.get('source_platform', '').lower()]
        
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    paginated = filtered[offset:offset+limit]
    
    return jsonify({
        "status": "success",
        "total_count": len(buyers),
        "filtered_count": len(filtered),
        "limit": limit,
        "offset": offset,
        "buyers": paginated
    })

@app.route('/api/buyers/search', methods=['POST'])
def api_search_buyers():
    """
    POST /api/buyers/search
    JSON Body or Form:
      {
         "keyword": "Singing Bowls",
         "max_results": 5,
         "platforms": ["google", "facebook", "linkedin", "directory"]
      }
    """
    data = request.get_json(silent=True) or request.form
    keyword = data.get("keyword", config.get("SEARCH_KEYWORD") or "Singing Bowls").strip()
    max_results = int(data.get("max_results", 5))
    
    raw_results = []
    # Query Google
    try:
        raw_results.extend(search_google(keyword, max_results))
    except Exception as e:
        print(f"[API] Google search error: {e}")
    # Query Facebook
    try:
        raw_results.extend(search_facebook(keyword, max_results))
    except Exception as e:
        print(f"[API] Facebook search error: {e}")
    # Query LinkedIn
    try:
        raw_results.extend(search_linkedin(keyword, max_results))
    except Exception as e:
        print(f"[API] LinkedIn search error: {e}")
    # Query Directory
    try:
        raw_results.extend(search_directory(keyword, max_results))
    except Exception as e:
        print(f"[API] Directory search error: {e}")
        
    normalized_records = []
    for item in raw_results:
        try:
            record = extract_and_normalize(item)
            if record.get('email') and is_valid_email(record.get('email')):
                normalized_records.append(record)
        except Exception as e:
            print(f"[API] Normalization error: {e}")
            
    new_added = write_buyers(normalized_records)
    
    return jsonify({
        "status": "success",
        "keyword": keyword,
        "raw_results_found": len(raw_results),
        "new_leads_added": new_added,
        "leads": normalized_records
    })

@app.route('/api/email/test', methods=['POST'])
def api_test_email():
    """
    POST /api/email/test
    Body:
      {
         "recipient": "recipient@example.com",
         "subject": "Optional Subject",
         "body": "Optional Body"
      }
    """
    data = request.get_json(silent=True) or request.form
    recipient = data.get("recipient", config.get("GMAIL_EMAIL")).strip()
    subject = data.get("subject", "Export Automation System — API Test Email").strip()
    body = data.get("body", "This is an automated API test email from the Export Automation System.").strip()
    
    attachment_path = os.path.join(config.BASE_DIR, 'assets', 'company_presentation.pdf')
    ok, message, status = send_single_email(recipient, subject, body, attachment_path)
    
    return jsonify({
        "status": "success" if ok else "error",
        "delivered": ok,
        "email_status": status,
        "message": message,
        "recipient": recipient
    }), (200 if ok else 400)

@app.route('/api/email/send', methods=['POST'])
def api_send_campaign():
    """
    POST /api/email/send
    Body:
      {
         "audience": "business" | "individual" | "all",
         "subject": "Subject Template with {company_name}",
         "body": "Body Template with {buyer_name}"
      }
    """
    data = request.get_json(silent=True) or request.form
    audience = data.get("audience", "business")
    subject = data.get("subject", config.get("DEFAULT_SUBJECT"))
    body = data.get("body", config.get("DEFAULT_BODY"))
    
    attachment_path = os.path.join(config.BASE_DIR, 'assets', 'company_presentation.pdf')
    result = run_outreach_campaign(
        subject_template=subject,
        body_template=body,
        audience=audience,
        attachment_path=attachment_path
    )
    
    return jsonify({
        "status": "error" if "error" in result else "success",
        "campaign_result": result
    })

@app.route('/api/generate-pitch', methods=['POST'])
def api_generate_pitch():
    """Generates an AI personalized B2B export pitch using Gemini."""
    from outreach.gemini_service import generate_export_pitch_with_gemini
    data = request.get_json(silent=True) or request.form
    buyer_name = data.get('buyer_name', 'Purchasing Manager')
    company_name = data.get('company_name', 'Partner Company')
    product_name = data.get('product_name', config.get('SEARCH_KEYWORD', 'Singing Bowls'))
    country = data.get('country', 'United States')
    
    pitch = generate_export_pitch_with_gemini(
        buyer_name=buyer_name,
        company_name=company_name,
        product_name=product_name,
        country=country
    )
    return jsonify(pitch)

@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """GET /api/stats: Overview metrics."""
    buyers = get_all_buyers()
    biz_emails, ind_emails = get_classified_emails()
    opted_out = get_opted_out_emails()
    stats = get_campaign_statistics()
    
    return jsonify({
        "status": "success",
        "total_buyers": len(buyers),
        "business_contacts": len(biz_emails),
        "individual_contacts": len(ind_emails),
        "opted_out_contacts": len(opted_out),
        "campaign_statistics": stats,
        "auth_mode": get_auth_mode(),
        "smtp_configured": is_smtp_configured()
    })

@app.route('/api-docs')
def api_docs():
    """Renders the Interactive API Explorer."""
    return render_template(
        'api_docs.html',
        active_page='api_docs',
        gmail_email=config.get("GMAIL_EMAIL")
    )

@app.route('/submission-guide')
def submission_guide():
    """Renders the HTML submission guide and 2-minute video script."""
    scratch_html = os.path.join(os.path.dirname(__file__), 'scratch_script.html')
    if os.path.exists(scratch_html):
        with open(scratch_html, 'r', encoding='utf-8') as f:
            return f.read()
    return "Submission guide not found", 404

@app.route('/download-guide')
def download_guide():
    """Opens or downloads the official 2-page PDF submission guide."""
    pdf_path = os.path.join(os.path.dirname(__file__), 'API_Export_Video_Script_and_Submission_Guide.pdf')
    if os.path.exists(pdf_path):
        return send_file(pdf_path, mimetype='application/pdf', as_attachment=False, download_name='API_Export_Video_Script_and_Submission_Guide.pdf')
    return "PDF file not found", 404

if __name__ == '__main__':
    print("=" * 65)
    print("      EXPORT AUTOMATION SYSTEM (API 3) — WEB DASHBOARD")
    print(f"      Running on: http://127.0.0.1:5000")
    print(f"      Auth Mode:  {get_auth_mode().upper()} ({config.get('GMAIL_EMAIL')})")
    print("=" * 65)
    app.run(host='127.0.0.1', port=5000, debug=True)
