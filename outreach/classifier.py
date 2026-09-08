import os
import json
from google import genai
from config import config
from activity_log.activity_logger import (
    get_all_buyers, 
    write_classified_emails, 
    get_classified_emails
)

# Common public consumer domains list for rule-based fallback and prompt reinforcement
PUBLIC_DOMAINS = {
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'aol.com', 
    'live.com', 'msn.com', 'icloud.com', 'mail.com', 'yandex.com', 
    'zoho.com', 'protonmail.com', 'gmx.com', 'mail.ru', 'mac.com'
}

def rule_based_classify(email):
    """Fallback rule-based classification of email domains."""
    if not email or '@' not in email:
        return 'individual'
    domain = email.split('@')[1].strip().lower()
    return 'individual' if domain in PUBLIC_DOMAINS else 'business'

def classify_emails_batch(emails):
    """
    Classify a batch of emails using Gemini API with fallback to rule-based logic.
    """
    api_key = config.get("GEMINI_API_KEY")
    
    if not api_key:
        print("[AI Classifier] Gemini API key not found in configuration. Running rule-based classifier...")
        return {email: rule_based_classify(email) for email in emails}
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = (
            "Classify the following email addresses into either 'business' or 'individual'.\n"
            "- 'business': Emails using custom business domains (e.g., info@soundhealingstore.com, procurement@soundbathco.com).\n"
            "- 'individual': Emails using public consumer mail domains (e.g., zenbath@gmail.com, tibetgifts@outlook.com).\n\n"
            "Return the output strictly as a JSON object mapping emails to labels, like this:\n"
            '{"email1@domain.com": "business", "email2@gmail.com": "individual"}\n'
            "Do not include any markdown styling, backticks, or explanation.\n\n"
            f"Emails to classify:\n{json.dumps(emails)}"
        )
        
        print(f"[AI Classifier] Sending batch of {len(emails)} emails to Gemini API...")
        model_candidates = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
        response = None
        for model_name in model_candidates:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    break
            except Exception:
                continue

        if not response or not response.text:
            raise RuntimeError("All Gemini model candidates failed in classifier.")
        text = response.text.strip()
        
        # Clean response if markdown blocks are returned
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        result = json.loads(text.strip())
        print(f"[AI Classifier] Gemini API successfully classified {len(result)} emails.")
        return result
        
    except Exception as e:
        print(f"[AI Classifier] Gemini API failed with error: {e}. Falling back to rule-based classification...")
        return {email: rule_based_classify(email) for email in emails}

def run_ai_classification(batch_size=10):
    """
    Reads buyers.csv, finds unique unclassified emails, 
    batches them, runs classification, and writes to CSVs.
    """
    print("[AI Classifier] Initializing classification run...")
    buyers = get_all_buyers()
    if not buyers:
        print("[AI Classifier] No buyers found in database to classify. Auto-sourcing leads...")
        try:
            from search import search_google, search_facebook, search_linkedin, search_directory
            from extraction import extract_and_normalize
            from validation import is_valid_email
            from config import config
            keyword = config.get("SEARCH_KEYWORD") or "Singing Bowls"
            raw_items = search_google(keyword, 4) + search_facebook(keyword, 4) + search_linkedin(keyword, 4) + search_directory(keyword, 4)
            norm = []
            for item in raw_items:
                rec = extract_and_normalize(item)
                if rec.get('email') and is_valid_email(rec.get('email')):
                    norm.append(rec)
            write_buyers(norm)
            buyers = get_all_buyers()
        except Exception as err:
            print(f"[AI Classifier] Auto-sourcing error: {err}")
            
    if not buyers:
        print("[AI Classifier] No buyers found in database.")
        biz, ind = get_classified_emails()
        return len(biz), len(ind)
        
    # Get unique, valid emails
    emails = list(set([b['email'].strip().lower() for b in buyers if b.get('email')]))
    
    # Get already classified emails to avoid redundant classification
    already_biz, already_ind = get_classified_emails()
    already_classified = already_biz.union(already_ind)
    
    unclassified_emails = [e for e in emails if e not in already_classified]
    
    if not unclassified_emails:
        print("[AI Classifier] All emails in database are already classified.")
        return len(already_biz), len(already_ind)
        
    print(f"[AI Classifier] Found {len(unclassified_emails)} new emails to classify. Batch size: {batch_size}")
    
    # Split into batches
    batches = [unclassified_emails[i:i + batch_size] for i in range(0, len(unclassified_emails), batch_size)]
    
    total_business = []
    total_individual = []
    
    for batch in batches:
        classifications = classify_emails_batch(batch)
        
        for email, label in classifications.items():
            if label == 'business':
                total_business.append(email)
            else:
                total_individual.append(email)
                
    # Write lists to CSVs
    write_classified_emails(total_business, total_individual)
    
    final_biz, final_ind = get_classified_emails()
    print(f"[AI Classifier] Run complete. Total classified: {len(final_biz)} business, {len(final_ind)} individual.")
    return len(final_biz), len(final_ind)
