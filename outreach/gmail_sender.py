import os
import sys
import time
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import config
from outreach.gmail_auth import (
    get_smtp_connection,
    get_gmail_service,
    is_smtp_configured,
    is_oauth_configured,
    get_auth_mode
)
from outreach.attachment_handler import create_attachment
from activity_log.activity_logger import (
    get_all_buyers,
    get_opted_out_emails,
    log_send_attempt,
    get_sent_logs,
    get_classified_emails
)

def build_message(sender_email, to_email, subject, body_text, attachment_path=None):
    """Create a MIME message with optional attachment."""
    message = MIMEMultipart()
    message['To'] = to_email
    message['From'] = f"Singing Bowls Export Outreach <{sender_email}>"
    message['Subject'] = subject
    
    # Attach email body text
    msg_body = MIMEText(body_text, 'plain', 'utf-8')
    message.attach(msg_body)
    
    # Attach presentation file if provided
    if attachment_path and os.path.exists(attachment_path):
        try:
            attachment = create_attachment(attachment_path)
            message.attach(attachment)
        except Exception as e:
            print(f"[Gmail Sender] Error attaching file {attachment_path}: {e}")
            
    return message

def send_smtp_message(server, sender_email, to_email, mime_msg):
    """Sends an email using an active authenticated SMTP server connection."""
    try:
        server.send_message(mime_msg)
        return True, "SMTP 250 Message accepted for delivery"
    except Exception as e:
        return False, str(e)

def send_gmail_api_message(service, sender_email, to_email, mime_msg):
    """Send an email using the Gmail API service (OAuth2)."""
    try:
        raw_msg = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode('utf-8')
        body = {'raw': raw_msg}
        send_result = service.users().messages().send(userId='me', body=body).execute()
        return True, send_result.get('id')
    except Exception as e:
        return False, str(e)

def count_sends_today():
    """Count how many emails were sent or simulated today."""
    logs = get_sent_logs()
    today_str = datetime.now().strftime("%Y-%m-%d")
    count = 0
    for entry in logs:
        if entry.get('timestamp', '').startswith(today_str):
            if entry.get('status') in ['sent', 'simulated']:
                count += 1
    return count

def send_single_email(to_email, subject, body_text, attachment_path=None):
    """
    Sends a single test email directly to the given address.
    Useful for immediate testing and capturing sent email screenshots.
    """
    sender_email = config.get("GMAIL_EMAIL") or "boddedavignesh3@gmail.com"
    physical_address = config.get("PHYSICAL_ADDRESS")
    
    # Anti-spam footer
    unsubscribe_link = f"mailto:{sender_email}?subject=Unsubscribe%20{to_email}&body=Please%20remove%20{to_email}%20from%20outreach%20campaigns."
    footer = (
        "\n\n---\n"
        f"This email was sent to {to_email} as part of the Export Automation System outreach.\n"
        f"Sender Address: {physical_address}\n"
        f"Unsubscribe: {unsubscribe_link}"
    )
    full_body = body_text + footer
    
    mime_msg = build_message(sender_email, to_email, subject, full_body, attachment_path)
    
    # 1. Try SMTP
    if is_smtp_configured():
        server, err = get_smtp_connection()
        if server:
            try:
                ok, msg_id = send_smtp_message(server, sender_email, to_email, mime_msg)
                server.quit()
                if ok:
                    log_send_attempt(to_email, subject, "sent")
                    return True, "Email sent successfully via Gmail SMTP!", "sent"
                else:
                    log_send_attempt(to_email, subject, "failed")
                    return False, f"SMTP send failed: {msg_id}", "failed"
            except Exception as e:
                return False, f"SMTP error: {str(e)}", "failed"
        else:
            return False, f"SMTP connection error: {err}", "failed"
            
    # 2. Try OAuth2
    service = get_gmail_service()
    if service:
        ok, msg_id = send_gmail_api_message(service, sender_email, to_email, mime_msg)
        if ok:
            log_send_attempt(to_email, subject, "sent")
            return True, f"Email sent via Gmail API! Message ID: {msg_id}", "sent"
        else:
            log_send_attempt(to_email, subject, "failed")
            return False, f"Gmail API error: {msg_id}", "failed"
            
    # 3. Fallback Simulation
    log_send_attempt(to_email, subject, "simulated")
    return True, "Simulated email dispatch (Simulation Mode).", "simulated"

def run_outreach_campaign(subject_template, body_template, audience, attachment_path=None):
    """
    Executes the campaign sending loop as per Section 12.3 Algorithm:
    - Reads leads from business / individual / all
    - Filters opted out
    - Sends via SMTP (with reconnect retry) or OAuth2 or Simulation
    - Respects daily limit and send delay
    """
    print(f"\n[Gmail Sender] Initializing outreach campaign for audience: '{audience}'...")
    
    buyers = get_all_buyers()
    if not buyers:
        print("[Gmail Sender] Error: No buyer leads found in database.")
        return {"error": "No buyers in database"}
        
    buyer_map = {b['email'].strip().lower(): b for b in buyers if b.get('email')}
    biz_emails, ind_emails = get_classified_emails()
    
    target_emails = []
    if audience == 'business':
        target_emails = list(biz_emails)
    elif audience == 'individual':
        target_emails = list(ind_emails)
    else:
        target_emails = list(buyer_map.keys())
        
    opted_out = get_opted_out_emails()
    send_queue = [email for email in target_emails if email not in opted_out]
    
    print(f"[Gmail Sender] Resolved {len(target_emails)} target emails. Filtered out {len(target_emails) - len(send_queue)} unsubscribed contacts.")
    
    if not send_queue:
        print("[Gmail Sender] Campaign aborted: Send queue is empty.")
        return {"error": "Send queue is empty"}
        
    if attachment_path and not os.path.exists(attachment_path):
        print(f"[Gmail Sender] Error: Specified attachment not found: {attachment_path}")
        return {"error": f"Attachment not found: {attachment_path}"}
        
    sender_email = config.get("GMAIL_EMAIL") or "boddedavignesh3@gmail.com"
    daily_limit = config.get("DAILY_SEND_LIMIT")
    sends_today = count_sends_today()
    remaining_sends = max(0, daily_limit - sends_today)
    
    auth_mode = get_auth_mode()
    mode = "production" if auth_mode in ("smtp", "oauth2") else "simulation"
    
    print(f"[Gmail Sender] Running in {auth_mode.upper()} mode.")
    print(f"[Gmail Sender] Today's Sends: {sends_today} / Daily Limit: {daily_limit}. Remaining sends allowed: {remaining_sends}")
    
    if remaining_sends <= 0:
        print("[Gmail Sender] Daily send limit reached. No emails will be sent today.")
        return {"error": "Daily send limit reached", "sends_today": sends_today, "limit": daily_limit}
        
    if len(send_queue) > remaining_sends:
        print(f"[Gmail Sender] Queue size ({len(send_queue)}) exceeds daily limit. Capping to {remaining_sends} recipients.")
        send_queue = send_queue[:remaining_sends]
        
    success_count = 0
    failed_count = 0
    results = []
    
    delay = config.get("SEND_DELAY")
    physical_address = config.get("PHYSICAL_ADDRESS")
    
    # Connect SMTP server if in SMTP mode
    smtp_server = None
    if auth_mode == "smtp":
        smtp_server, err = get_smtp_connection()
        if not smtp_server:
            print(f"[Gmail Sender] SMTP connection failed: {err}. Falling back to simulation.")
            auth_mode = "simulation"
            mode = "simulation"
            
    # Connect Gmail API service if in OAuth2 mode
    gmail_service = None
    if auth_mode == "oauth2":
        gmail_service = get_gmail_service()
        if not gmail_service:
            print("[Gmail Sender] OAuth service failed. Falling back to simulation.")
            auth_mode = "simulation"
            mode = "simulation"
            
    try:
        for i, email in enumerate(send_queue):
            # Synchronously check opt-out list immediately before sending each email
            if email in get_opted_out_emails():
                print(f"[Gmail Sender] Recipient {email} opted out during campaign run. Skipping.")
                continue

            if i > 0 and delay > 0:
                print(f"[Gmail Sender] Waiting {delay}s to avoid rate limiting...")
                time.sleep(delay)
                
            buyer = buyer_map.get(email, {})
            # Sanitize against CRLF email header injection
            import re
            clean_buyer_name = re.sub(r'[\r\n]+', ' ', str(buyer.get("buyer_name", "")).strip())[:80] or "Purchasing Manager"
            clean_company_name = re.sub(r'[\r\n]+', ' ', str(buyer.get("company_name", "")).strip())[:100] or "your business"
            clean_platform = re.sub(r'[\r\n]+', ' ', str(buyer.get("source_platform", "")).strip())[:50] or "our online search"
            
            subject = subject_template.format(
                buyer_name=clean_buyer_name,
                company_name=clean_company_name,
                source_platform=clean_platform
            )
            subject = re.sub(r'[\r\n]+', '', subject).strip()
            
            body_content = body_template.format(
                buyer_name=clean_buyer_name,
                company_name=clean_company_name,
                source_platform=clean_platform
            )
            
            unsubscribe_link = f"mailto:{sender_email}?subject=Unsubscribe%20{email}&body=Please%20remove%20{email}%20from%20outreach%20campaigns."
            footer = (
                "\n\n---\n"
                f"This email was sent to {email} because your business was listed on {clean_platform}.\n"
                f"Sender Address: {physical_address}\n"
                f"If you wish to stop receiving these offers, please click here to unsubscribe:\n"
                f"{unsubscribe_link}"
            )
            full_body = body_content + footer
            
            mime_msg = build_message(
                sender_email=sender_email,
                to_email=email,
                subject=subject,
                body_text=full_body,
                attachment_path=attachment_path
            )
            
            status = "failed"
            if auth_mode == "smtp" and smtp_server:
                print(f"[Gmail Sender] Sending real email via SMTP to {email}...")
                try:
                    ok, resp = send_smtp_message(smtp_server, sender_email, email, mime_msg)
                    if not ok:
                        # Reconnect retry on failure/disconnection
                        print(f"[Gmail Sender] Reconnecting SMTP session...")
                        smtp_server, _ = get_smtp_connection()
                        if smtp_server:
                            ok, resp = send_smtp_message(smtp_server, sender_email, email, mime_msg)
                    if ok:
                        status = "sent"
                        success_count += 1
                        print(f"[Gmail Sender] Sent successfully via SMTP to {email}!")
                    else:
                        status = "failed"
                        failed_count += 1
                        print(f"[Gmail Sender] Send failed to {email}: {resp}")
                except Exception as e:
                    status = "failed"
                    failed_count += 1
                    print(f"[Gmail Sender] Exception sending to {email}: {e}")
                    
            elif auth_mode == "oauth2" and gmail_service:
                print(f"[Gmail Sender] Sending real email via Gmail API to {email}...")
                ok, response_info = send_gmail_api_message(gmail_service, sender_email, email, mime_msg)
                if ok:
                    status = "sent"
                    success_count += 1
                    print(f"[Gmail Sender] Sent successfully! Message ID: {response_info}")
                else:
                    status = "failed"
                    failed_count += 1
                    print(f"[Gmail Sender] Send failed.")
            else:
                # Simulation mode
                print(f"\n================ SIMULATION SEND ({i+1}/{len(send_queue)}) ================")
                print(f"To: {email}")
                print(f"Subject: {subject}")
                print(f"Body:\n{full_body}")
                if attachment_path:
                    print(f"Attachment: {os.path.basename(attachment_path)} (packaged successfully)")
                print("=============================================================")
                status = "simulated"
                success_count += 1
                
            log_send_attempt(email, subject, status)
            results.append({
                "email": email,
                "status": status,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
    finally:
        if smtp_server:
            try:
                smtp_server.quit()
            except Exception:
                pass
                
    print(f"\n[Gmail Sender] Campaign finished. Successful: {success_count}, Failed: {failed_count}.")
    
    return {
        "mode": mode,
        "auth_mode": auth_mode,
        "total_attempted": len(send_queue),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }
