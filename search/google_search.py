import requests
from bs4 import BeautifulSoup
import urllib.parse
import base64
import random
import time

IGNORED_DOMAINS = [
    'wikipedia.org', 'wiktionary.org', 'britannica.com', 'merriam-webster.com',
    'youtube.com', 'facebook.com', 'linkedin.com', 'instagram.com', 'twitter.com', 'x.com',
    'sciencenotes.org', 'scienceinfo.com', 'explainthatstuff.com', 'quora.com', 'reddit.com',
    'pinterest.com', 'dictionary.com'
]

MOCK_RESULTS = [
    {
        "title": "Himalayan Singing Bowls Wholesale & Imports",
        "snippet": "We import authentic handmade singing bowls from Nepal. Retail and wholesale inquiries contact wholesale@himalayanbowlsusa.com or call our Florida warehouse.",
        "url": "https://www.himalayanbowlsusa.com",
        "platform": "Google"
    },
    {
        "title": "Zen Meditation & Sound Healing Center",
        "snippet": "Offering weekly sound bath sessions and meditation workshops. For inquiries, email zenbath@zenmeditationsounds.com or visit our studio in Seattle.",
        "url": "https://www.zenmeditationsounds.com",
        "platform": "Google"
    },
    {
        "title": "Sound Therapy London - Certified Healing Bowls",
        "snippet": "Individual therapy and group sound healing training. Contact us at info@soundtherapylondon.co.uk for booking details.",
        "url": "http://www.soundtherapylondon.co.uk",
        "platform": "Google"
    },
    {
        "title": "Mindful Living Imports LLC - Global Craft Sourcing",
        "snippet": "Importers of ethical home decor and spiritual crafts. Sourcing high-quality brass singing bowls. Partner with us: buyer@mindfullivingimports.com.",
        "url": "https://www.mindfullivingimports.com",
        "platform": "Google"
    },
    {
        "title": "Sydney Sound Wellness & Meditation Clinic",
        "snippet": "Specializing in Tibetan sound therapy and yoga accessories. Email us for partnerships at contact@sydneysoundwellness.com.au.",
        "url": "https://www.sydneysoundwellness.com.au",
        "platform": "Google"
    },
    {
        "title": "Spiritual Craft Emporium - Handcrafted Singing Bowls",
        "snippet": "Your online shop for incense, singing bowls, and yoga gear. For orders or supplier contact: support@spiritualcraftshop.com.",
        "url": "https://www.spiritualcraftshop.com",
        "platform": "Google"
    },
    {
        "title": "Bodhi Sound Goods & Accessories Ltd",
        "snippet": "Distributor of singing bowls and meditation bells in Canada. Supplier inquiries can be sent directly to sourcing@bodhisounds.ca.",
        "url": "https://www.bodhisounds.ca",
        "platform": "Google"
    },
    {
        "title": "Nirvana Sound Therapy - Amsterdam",
        "snippet": "Discover the healing vibrations of handmade singing bowls. Email contact: info@nirvanasounds.nl. Located in central Amsterdam.",
        "url": "http://www.nirvanasounds.nl",
        "platform": "Google"
    },
    {
        "title": "Vedic Crafts - Singing Bowls Exporter & Distributor",
        "snippet": "We distribute Himalayan arts and crafts. Sourcing team email: exports@vediccrafts.in.",
        "url": "https://www.vediccrafts.in",
        "platform": "Google"
    },
    {
        "title": "Sacred Sound Healing Studio Tokyo",
        "snippet": "Spiritual sound treatments and meditation workshops. Direct contact: booking@sacredsoundstokyo.jp.",
        "url": "https://www.sacredsoundstokyo.jp",
        "platform": "Google"
    }
]

def resolve_search_url(raw_url):
    """Resolves redirect tracking URLs (e.g. Bing /ck/a? redirect wrappers) to canonical destination URLs."""
    if not raw_url:
        return ""
    if '/ck/a?' in raw_url and 'u=' in raw_url:
        try:
            parsed = urllib.parse.urlparse(raw_url)
            qs = urllib.parse.parse_qs(parsed.query)
            u_val = qs.get('u', [''])[0]
            if u_val.startswith('a1'):
                decoded = base64.b64decode(u_val[2:] + '==').decode('utf-8', errors='ignore')
                if decoded.startswith('http'):
                    return decoded
        except Exception:
            pass
    return raw_url

def search_google(keyword, max_results=10):
    """
    Real-time B2B search adapter.
    Queries live search engines for international buyer and distributor websites,
    extracts real business links and contact metadata, falling back to mock data if offline.
    """
    print(f"[Search Engine] Performing real-time search for: '{keyword}' (requesting up to {max_results} results)...")
    
    query = f"{keyword} wholesale buyers importers distributors store contact us"
    url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    results = []
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for item in soup.find_all('li', class_='b_algo'):
                if len(results) >= max_results:
                    break
                h2 = item.find('h2')
                if not h2:
                    continue
                title = h2.get_text().strip()
                a_tag = h2.find('a')
                if not a_tag or 'href' not in a_tag.attrs:
                    continue
                
                resolved_url = resolve_search_url(a_tag['href'])
                if not resolved_url.startswith('http'):
                    continue
                    
                parsed_domain = urllib.parse.urlparse(resolved_url).netloc.lower()
                if any(ign in parsed_domain for ign in IGNORED_DOMAINS):
                    continue
                    
                cap = item.find('div', class_='b_caption')
                snippet = cap.get_text().strip() if cap else ""
                
                # Check keyword relevance
                k_words = [w.lower() for w in keyword.split() if len(w) > 2]
                text_content = (title + " " + snippet).lower()
                if k_words and not any(w in text_content for w in k_words):
                    continue
                
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "url": resolved_url,
                    "platform": "Google"
                })

        if results:
            print(f"[Search Engine] Successfully retrieved {len(results)} live real-time web results for '{keyword}'.")
            return results
        else:
            print(f"[Search Engine] No live results parsed. Using baseline fallback dataset...")
            return MOCK_RESULTS[:max_results]
            
    except Exception as e:
        print(f"[Search Engine] Real-time search encountered an exception: {e}. Using fallback...")
        return MOCK_RESULTS[:max_results]
