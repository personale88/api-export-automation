import os
import json
from config import config

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

PUBLIC_DOMAINS = {
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'aol.com', 
    'live.com', 'msn.com', 'icloud.com', 'mail.com', 'yandex.com', 
    'zoho.com', 'protonmail.com', 'gmx.com', 'mail.ru', 'mac.com'
}

def get_gemini_client():
    """Returns an authenticated Gemini client if API key is configured."""
    api_key = config.get("GEMINI_API_KEY", "").strip()
    if not api_key or not HAS_GENAI:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[Gemini Service] Failed to initialize Gemini client: {e}")
        return None

def classify_emails_with_gemini(emails):
    """
    Classifies a list of emails into 'business' or 'individual' using Gemini AI.
    Falls back to domain heuristics if API key is not present or if call fails.
    """
    client = get_gemini_client()
    if not client:
        return {
            email: ('individual' if email.split('@')[1].lower() in PUBLIC_DOMAINS else 'business')
            for email in emails if '@' in email
        }

    prompt = (
        "Classify each of the following email addresses into either 'business' or 'individual'.\n"
        "- 'business': Emails using corporate/domain addresses (e.g. procurement@soundbath.com, sales@company.co.uk).\n"
        "- 'individual': Emails using public consumer mailboxes (e.g. user@gmail.com, contact@yahoo.com).\n\n"
        "Return strictly a raw JSON dictionary mapping email to classification, like:\n"
        '{"user@domain.com": "business"}\n'
        "No explanation, no markdown backticks.\n\n"
        f"Emails:\n{json.dumps(emails)}"
    )

    try:
        print(f"[Gemini AI] Classifying batch of {len(emails)} emails with Gemini...")
        model_candidates = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
        response = None
        for model_name in model_candidates:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                if response and response.text:
                    break
            except Exception:
                continue
        if not response or not response.text:
            raise RuntimeError("All Gemini model candidates failed.")
            
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        return json.loads(raw_text.strip())
    except Exception as e:
        print(f"[Gemini AI] Classification call failed ({e}), using heuristics...")
        return {
            email: ('individual' if email.split('@')[1].lower() in PUBLIC_DOMAINS else 'business')
            for email in emails if '@' in email
        }

def generate_export_pitch_with_gemini(buyer_name="Purchasing Manager", company_name="Partner Company", product_name="Handcrafted Singing Bowls", country="United States"):
    """
    Generates a personalized B2B cold export sales pitch using Gemini AI.
    """
    client = get_gemini_client()
    catalog_name = os.path.basename(config.get("PRESENTATION_PATH", "company_presentation.pdf"))

    if not client:
        return {
            "source": "Smart Template (Add Gemini Key for Live AI Generation)",
            "subject": f"Wholesale Supply Partnership for {product_name} — {company_name}",
            "body": (
                f"Dear {buyer_name},\n\n"
                f"I hope this message finds you well at {company_name}.\n\n"
                f"We are direct manufacturers and exporters specializing in authentic, export-grade {product_name}. "
                f"We supply leading retail boutiques, wellness centers, and international distributors across {country} with reliable factory-direct pricing.\n\n"
                f"I have attached our official wholesale presentation catalog ({catalog_name}) showcasing our latest product specifications, certification, and volume tiered discounts.\n\n"
                f"Would you be open to a quick 5-minute call or reviewing a custom sample package for {company_name} this week?\n\n"
                f"Best regards,\nExport Sales Director\nExport Automation Hub"
            )
        }

    prompt = (
        f"You are an expert B2B International Export Sales Director. Write a compelling, high-converting cold outreach email.\n"
        f"Details:\n"
        f"- Recipient: {buyer_name} at {company_name}\n"
        f"- Target Country: {country}\n"
        f"- Export Product: {product_name}\n"
        f"- Attachment: Mention that our company presentation catalog ({catalog_name}) is attached.\n"
        f"- Requirements: Keep the email under 130 words. Friendly, persuasive, professional B2B tone. Clear call to action.\n"
        f"- Output Format: Return strictly in this exact format:\n"
        f"SUBJECT: <write subject line here>\n"
        f"BODY:\n<write body here>"
    )

    try:
        print(f"[Gemini AI] Generating personalized export outreach pitch for {company_name}...")
        model_candidates = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
        response = None
        used_model = 'gemini-3.6-flash'
        for model_name in model_candidates:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                if response and response.text:
                    used_model = model_name
                    break
            except Exception:
                continue

        if not response or not response.text:
            raise RuntimeError("All Gemini model candidates failed for pitch generation.")

        text = response.text.strip()
        subject = f"Wholesale {product_name} Partnership — {company_name}"
        body = text

        if "SUBJECT:" in text and "BODY:" in text:
            parts = text.split("BODY:", 1)
            subject = parts[0].replace("SUBJECT:", "").strip()
            body = parts[1].strip()

        return {
            "source": f"Google Gemini AI ({used_model})",
            "subject": subject,
            "body": body
        }
    except Exception as e:
        print(f"[Gemini AI] Pitch generation encountered error: {e}")
        return {
            "source": "Fallback Template",
            "subject": f"Direct Export Opportunity: {product_name} for {company_name}",
            "body": (
                f"Dear {buyer_name},\n\n"
                f"We are pleased to connect with {company_name} regarding direct factory supply of {product_name}.\n\n"
                f"Please find our wholesale catalog ({catalog_name}) attached for your review. Let us know if you would like a price quotation."
            )
        }
