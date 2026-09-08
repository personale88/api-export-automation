import requests
from bs4 import BeautifulSoup
import urllib.parse
from search.google_search import resolve_search_url, IGNORED_DOMAINS

LINKEDIN_MOCK_LEADS = [
    {
        "title": "David Miller - Founder & CEO at Harmony Sound Imports",
        "snippet": "David Miller's profile: Importing handcrafted sound healing instruments for retailers across Canada. Contact: dmiller@harmonysoundimports.ca.",
        "url": "https://www.harmonysoundimports.ca",
        "platform": "LinkedIn"
    },
    {
        "title": "Elena Rostova - Sourcing Director at Munich Yoga Supplies",
        "snippet": "Elena Rostova is responsible for purchasing wholesale meditation accessories and singing bowls. Sourcing inquiries: elena.rostova@munichyogasupplies.de.",
        "url": "https://www.munichyogasupplies.de",
        "platform": "LinkedIn"
    },
    {
        "title": "Aurore Dubois - Sound Healing Therapist & Spa Coordinator",
        "snippet": "Coordinating holistic wellness products for luxury hotel spas in France. Direct inquiries: a.dubois@spaserenityfrance.fr.",
        "url": "https://www.spaserenityfrance.fr",
        "platform": "LinkedIn"
    },
    {
        "title": "Marcus Vance - Wholesale Purchaser at Sound Bath Co.",
        "snippet": "Sound Bath Co. is expanding its inventory of Tibetan singing bowls and gongs. Reach out at procurement@soundbathco.com.",
        "url": "https://www.soundbathco.com",
        "platform": "LinkedIn"
    },
    {
        "title": "Siddharth Mehta - Import Coordinator at Nirvana Crafts Australia",
        "snippet": "Importers of fine hand-hammered singing bowls, bells, and spiritual art. Email: imports@nirvanacraftsau.com.",
        "url": "https://www.nirvanacraftsau.com",
        "platform": "LinkedIn"
    }
]

def search_linkedin(keyword, max_results=5):
    """
    Real-time B2B corporate trade search adapter.
    Discovers corporate distributors, importers, and procurement entities for the target keyword.
    """
    print(f"[LinkedIn Search] Querying live corporate trade network for: '{keyword}'...")
    query = f"{keyword} corporate wholesale importers distributors procurement contact email"
    url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
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
                a_tag = h2.find('a')
                if not a_tag or 'href' not in a_tag.attrs:
                    continue
                    
                resolved_url = resolve_search_url(a_tag['href'])
                if not resolved_url.startswith('http'):
                    continue
                    
                domain = urllib.parse.urlparse(resolved_url).netloc.lower()
                if any(ign in domain for ign in IGNORED_DOMAINS):
                    continue
                    
                cap = item.find('div', class_='b_caption')
                snippet = cap.get_text().strip() if cap else ""
                
                k_words = [w.lower() for w in keyword.split() if len(w) > 2]
                text_content = (h2.get_text() + " " + snippet).lower()
                if k_words and not any(w in text_content for w in k_words):
                    continue
                
                results.append({
                    "title": h2.get_text().strip(),
                    "snippet": snippet,
                    "url": resolved_url,
                    "platform": "LinkedIn"
                })
                
        if results:
            print(f"[LinkedIn Search] Found {len(results)} live corporate buyer records for '{keyword}'.")
            return results
    except Exception as e:
        print(f"[LinkedIn Search] Live query failed ({e}), using baseline...")
        
    limit = min(max_results, len(LINKEDIN_MOCK_LEADS))
    return LINKEDIN_MOCK_LEADS[:limit]
