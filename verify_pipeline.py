import os
import sys

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add current folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from search import search_google, search_facebook, search_linkedin, search_directory
from extraction import extract_and_normalize
from validation import is_valid_email
from activity_log.activity_logger import (
    clear_database,
    get_all_buyers,
    get_classified_emails,
    get_opted_out_emails,
    add_opt_out
)
from outreach.classifier import run_ai_classification
from outreach.gmail_sender import run_outreach_campaign
from reports import get_campaign_statistics, get_last_run_statistics

def test_pipeline():
    print("=" * 60)
    print("      INTEGRATION VERIFICATION FOR API 3 PIPELINE")
    print("=" * 60)
    
    # 1. Reset database for clean testing
    print("\n[Step 1] Clearing databases for clean testing...")
    clear_database()
    assert len(get_all_buyers()) == 0, "Database clearing failed!"
    print("✓ Databases cleared successfully.")
    
    # 2. Config verification
    print("\n[Step 2] Verifying configuration...")
    keyword = config.get("SEARCH_KEYWORD")
    daily_limit = config.get("DAILY_SEND_LIMIT")
    print(f"Loaded config: Keyword='{keyword}', Daily Send Limit={daily_limit}")
    assert keyword is not None, "Configuration keyword missing!"
    print("✓ Configurations verified.")
    
    # 3. Search and Extraction verification
    print("\n[Step 3] Verifying Search Adapters & Data Extractor...")
    g_results = search_google("Singing Bowls", max_results=2)
    assert len(g_results) > 0, "Google search adapter returned empty!"
    print(f"Search Google: Found {len(g_results)} results.")
    
    raw_item = g_results[0]
    print(f"Extracted Raw Item Sample: {raw_item}")
    
    # Extraction & normalization
    normalized = extract_and_normalize(raw_item)
    assert normalized.get('email') is not None, "Normalized record missing email key!"
    assert normalized.get('company_name') != "Unknown Company", "Company name cleaning failed!"
    print("✓ Search and extraction components verified.")
    
    # 4. Email validation verification
    print("\n[Step 4] Verifying Email Validator...")
    valid_email = "sales@company.com"
    invalid_email1 = "hello@verylongdomainnamepaththatshouldbecompletelyinvalidforouremaillengthcheck.com"
    invalid_email2 = "image@company.com/page.jpg"
    invalid_email3 = "not-an-email"
    
    assert is_valid_email(valid_email) is True, f"Failed on valid email: {valid_email}"
    assert is_valid_email(invalid_email1) is False, f"Allowed long domain email: {invalid_email1}"
    assert is_valid_email(invalid_email2) is False, f"Allowed image email: {invalid_email2}"
    assert is_valid_email(invalid_email3) is False, f"Allowed malformed syntax email: {invalid_email3}"
    print("✓ Email Validator verified (all edge cases filtered).")
    
    # 5. Run full simulation discovery write
    print("\n[Step 5] Populating database via Discovery run simulation...")
    # Inject test mock leads
    from activity_log.activity_logger import write_buyers
    test_leads = [
        {
            "buyer_name": "John Doe",
            "company_name": "Sound Bath Studio NY",
            "email": "john@soundbathny.com",
            "website": "https://soundbathny.com",
            "country": "United States",
            "source_platform": "Google",
            "source_url": "https://soundbathny.com"
        },
        {
            "buyer_name": "Mary Jane",
            "company_name": "Aura Wellness UK",
            "email": "mary.jane@gmail.com",
            "website": "https://aurawellness.co.uk",
            "country": "United Kingdom",
            "source_platform": "Facebook",
            "source_url": "https://facebook.com/aurawellness"
        }
    ]
    added = write_buyers(test_leads)
    assert added == 2, f"Failed to populate test leads! Added: {added}"
    print(f"✓ Sourced and saved {added} valid leads.")
    
    # 6. Classification verification
    print("\n[Step 6] Running AI Classification simulation...")
    biz_count, ind_count = run_ai_classification(batch_size=2)
    print(f"Classified: {biz_count} business and {ind_count} individual emails.")
    
    biz_emails, ind_emails = get_classified_emails()
    assert "john@soundbathny.com" in biz_emails, "John should be classified as business (custom domain)!"
    assert "mary.jane@gmail.com" in ind_emails, "Mary should be classified as individual (gmail domain)!"
    print("✓ AI Classifier verified (correctly split domain namespaces).")
    
    # 7. Unsubscribe check
    print("\n[Step 7] Checking anti-spam opt-out compliance...")
    add_opt_out("john@soundbathny.com")
    opted_out = get_opted_out_emails()
    assert "john@soundbathny.com" in opted_out, "Failed to register unsubscribe request!"
    print("✓ Anti-spam list registration verified.")
    
    # 8. Campaign Outreach simulation
    print("\n[Step 8] Triggering Outreach Campaign (Simulation Mode)...")
    result = run_outreach_campaign(
        subject_template="Sound Bath Offer for {company_name}",
        body_template="Hello {buyer_name},\nWe found you on {source_platform}.",
        audience="business",
        attachment_path=os.path.join(config.BASE_DIR, 'assets', 'company_presentation.pdf')
    )
    
    # John is unsubscribed, so the queue for business (which is just John) should filter him out and be empty!
    # Let's verify this behavior:
    assert result.get("error") == "Send queue is empty", f"Did not skip unsubscribed contact! Result: {result}"
    print("✓ Verified campaign successfully filtered out unsubscribed contact.")
    
    # Try sending to 'individual' (Mary)
    result_ind = run_outreach_campaign(
        subject_template="Catalog for {company_name}",
        body_template="Hello {buyer_name}.",
        audience="individual",
        attachment_path=os.path.join(config.BASE_DIR, 'assets', 'company_presentation.pdf')
    )
    assert result_ind.get("success_count") == 1, "Simulation dispatch failed!"
    print("✓ Verified outreach dispatch and simulation console formatting.")
    
    # 9. Report generator check
    print("\n[Step 9] Verifying Reporting modules...")
    stats = get_campaign_statistics()
    last_run = get_last_run_statistics()
    
    assert stats.get("total") == 1, "Outbox history count incorrect!"
    assert last_run.get("success") == 1, "Last run statistics incorrect!"
    print(f"Stats - Total Sends: {stats['total']}, Success Rate: {stats['success_rate']}%")
    print("✓ Reporting engine verified.")
    
    print("\n" + "=" * 60)
    print("      ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == '__main__':
    test_pipeline()
