import os
import re
from datetime import datetime
import urllib.parse
from search.website_search import extract_emails_from_text, crawl_website_for_emails

# Common TLD to Country mappings
TLD_COUNTRY_MAP = {
    ".uk": "United Kingdom",
    ".co.uk": "United Kingdom",
    ".de": "Germany",
    ".nl": "Netherlands",
    ".ca": "Canada",
    ".au": "Australia",
    ".com.au": "Australia",
    ".sg": "Singapore",
    ".jp": "Japan",
    ".co.in": "India",
    ".in": "India",
    ".fr": "France",
    ".us": "United States"
}

# Country keyword matching in text
COUNTRY_KEYWORDS = {
    "United States": ["usa", "united states", "seattle", "denver", "new york", "florida", "nyc", "sf", "san francisco", "chicago"],
    "United Kingdom": ["uk", "united kingdom", "london", "manchester"],
    "Germany": ["germany", "munich", "berlin", "deutschland"],
    "Netherlands": ["netherlands", "amsterdam", "holland"],
    "Canada": ["canada", "vancouver", "toronto"],
    "Australia": ["australia", "sydney", "melbourne"],
    "Singapore": ["singapore"],
    "Japan": ["japan", "tokyo", "kyoto"],
    "India": ["india", "delhi", "mumbai"],
    "France": ["france", "paris"]
}

def clean_company_name(title, url):
    """Infer a clean company name from the title or domain name."""
    if not title:
        return "Unknown Company"
        
    # Standard cleaning (remove platform suffixes, etc)
    company = title.split("-")[0].split("|")[0].split("—")[0].strip()
    
    # Remove generic social site extensions if title is messy
    if company.lower() in ["facebook", "linkedin", "google", "directory listing", "log in", "sign up"]:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        company = domain.split(".")[0].replace("-", " ").title()
        
    # Limit length
    if len(company) > 60:
        company = company[:57] + "..."
        
    return company

def infer_buyer_name(snippet, title):
    """Infer a person's name or fall back to a generic business development title."""
    # Look for common name patterns or words like "David Miller", "Elena Rostova", "Sarah Jenkins"
    # For simplicity, search for known indicators in mock data first, else use standard fallback
    text = f"{title} {snippet}"
    
    # Simple rule-based extraction for known mock structures
    name_match = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+) (?:-|is responsible|post by|profile:)', text)
    if name_match:
        name = name_match.group(1)
        # Avoid matching generic terms
        if name.lower() not in ["singing bowls", "sound healing", "tibetan singing", "meditation arts"]:
            return name
            
    # Look for "post by X"
    post_match = re.search(r'post by ([A-Z][a-z]+ [A-Z][a-z]+)', text, re.IGNORECASE)
    if post_match:
        return post_match.group(1)
        
    return "Purchasing Manager"

def infer_country(snippet, title, url):
    """Infer country of the lead based on URL TLD and text snippets."""
    text = f"{title} {snippet}".lower()
    
    # Check URL TLD first
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    for tld, country in TLD_COUNTRY_MAP.items():
        if domain.endswith(tld):
            return country
            
    # Check text snippets for keywords
    for country, keywords in COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                return country
                
    return "United States" # Default fallback for general .com leads

def extract_and_normalize(raw_item):
    """
    Takes a raw search result item, extracts necessary fields,
    scrapes the website if no email is in the snippet,
    and returns a normalized buyer record.
    """
    title = raw_item.get("title", "")
    snippet = raw_item.get("snippet", "")
    url = raw_item.get("url", "")
    platform = raw_item.get("platform", "Google")
    
    print(f"\n[Data Extractor] Normalizing lead: '{title}' from {platform}...")
    
    # 1. Clean Company Name
    company_name = clean_company_name(title, url)
    
    # 2. Infer Buyer Name
    buyer_name = infer_buyer_name(snippet, title)
    
    # 3. Infer Country
    country = infer_country(snippet, title, url)
    
    # 4. Extract Email
    # Try finding email directly in the snippet to avoid HTTP requests
    emails = extract_emails_from_text(snippet)
    
    if not emails and url.startswith("http"):
        # Crawl the website to find email addresses
        emails = crawl_website_for_emails(url)
        
    email = emails[0] if emails else ""
    
    record = {
        "buyer_name": buyer_name,
        "company_name": company_name,
        "email": email,
        "website": url,
        "country": country,
        "source_platform": platform,
        "source_url": url,
        "discovered_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print(f"[Data Extractor] Normalized: {record['buyer_name']} | {record['company_name']} | Email: {record['email']} | Country: {record['country']}")
    return record
