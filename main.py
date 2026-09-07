import argparse
import sys
import os

# Add root folder to sys.path to resolve package imports when running as script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from app import app
from search import search_google, search_facebook, search_linkedin, search_directory
from extraction import extract_and_normalize
from validation import is_valid_email
from activity_log.activity_logger import write_buyers, get_all_buyers
from outreach import run_ai_classification, run_outreach_campaign
from reports import get_last_run_statistics

def run_cli_pipeline(keyword, max_results):
    """
    Executes the full pipeline sequentially in CLI mode:
    1. Lead Search (Google, Facebook, LinkedIn, Directories)
    2. Data Extraction & Normalization
    3. Email Validation
    4. AI Email Classification (Business vs Individual)
    5. Gmail Outreach (OAuth2 with compliance)
    6. Run Summary Report
    """
    print("=" * 60)
    print("      EXPORT AUTOMATION PIPELINE (CLI MODE)")
    print("=" * 60)
    
    # Update search keyword in settings
    config.update({"SEARCH_KEYWORD": keyword})
    
    # --- STAGE 1 & 2: DISCOVERY & EXTRACTION ---
    print("\n--- STAGE 1: Discovering Buyers ---")
    g_raw = search_google(keyword, max_results)
    fb_raw = search_facebook(keyword, max_results)
    li_raw = search_linkedin(keyword, max_results)
    dir_raw = search_directory(keyword, max_results)
    
    all_raw = g_raw + fb_raw + li_raw + dir_raw
    print(f"Collected {len(all_raw)} raw listings. Normalizing leads...")
    
    normalized = []
    for item in all_raw:
        try:
            record = extract_and_normalize(item)
            if record.get('email'):
                normalized.append(record)
        except Exception as e:
            print(f"[CLI Pipeline] Extraction error: {e}")
            
    # --- STAGE 3: VALIDATION ---
    print("\n--- STAGE 2: Validating Emails ---")
    valid_records = []
    invalid_count = 0
    for r in normalized:
        email = r.get('email', '')
        if is_valid_email(email):
            valid_records.append(r)
        else:
            invalid_count += 1
            print(f"[CLI Pipeline] Discarding invalid email: {email}")
            
    # Save to buyers database
    new_added = write_buyers(valid_records)
    print(f"Validation finished. Added {new_added} new valid leads. Discarded {invalid_count} malformed/invalid emails.")
    
    # --- STAGE 4: CLASSIFICATION ---
    print("\n--- STAGE 3: Segmenting Contacts (AI Classification) ---")
    biz_added, ind_added = run_ai_classification(batch_size=10)
    print(f"Segmented: {biz_added} new business, {ind_added} new individual contacts added to stores.")
    
    # --- STAGE 5: GMAIL OUTREACH ---
    print("\n--- STAGE 4: Launching Outreach Campaign ---")
    # Retrieve campaign templates from config
    subject = config.get("DEFAULT_SUBJECT")
    body = config.get("DEFAULT_BODY")
    attachment_path = os.path.join(config.BASE_DIR, 'assets', 'company_presentation.pdf')
    
    # Send to business accounts by default for anti-spam safety
    outreach_results = run_outreach_campaign(
        subject_template=subject,
        body_template=body,
        audience='business',
        attachment_path=attachment_path
    )
    
    if "error" in outreach_results:
        print(f"Outreach aborted: {outreach_results['error']}")
        return
        
    # --- STAGE 6: REPORTING ---
    print("\n--- STAGE 5: Summary Report ---")
    last_run = get_last_run_statistics()
    print("-" * 40)
    print(f"Campaign: {last_run.get('campaign_name')}")
    print(f"Mode: {outreach_results.get('mode').upper()}")
    print(f"Total Attempted: {last_run.get('total')}")
    print(f"Successful Dispatches: {last_run.get('success')}")
    print(f"Failed Sends: {last_run.get('failed')}")
    print(f"Campaign Success Rate: {last_run.get('success_rate')}%")
    print("-" * 40)
    print("\nPipeline execution completed successfully!")

def main():
    parser = argparse.ArgumentParser(description="Singing Bowls EXPORT Automation System (API 3)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--web', action='store_true', help="Start the Flask Web App dashboard (Default)")
    group.add_argument('--cli', action='store_true', help="Run the pipeline sequentially via the terminal command line interface")
    
    parser.add_argument('--keyword', type=str, default="Singing Bowls", help="Keyword search query (CLI mode only)")
    parser.add_argument('--max-results', type=int, default=3, help="Max search results per adapter (CLI mode only)")
    
    args = parser.parse_args()
    
    if args.cli:
        run_cli_pipeline(args.keyword, args.max_results)
    else:
        # Default behavior: run the Flask web application
        print(f"Starting Singing Bowls Export Automation web server on http://127.0.0.1:5000 ...")
        app.run(host='127.0.0.1', port=5000, debug=True)

if __name__ == '__main__':
    main()
