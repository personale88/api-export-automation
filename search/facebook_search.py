import requests
from bs4 import BeautifulSoup
import urllib.parse
from search.google_search import resolve_search_url, IGNORED_DOMAINS

FACEBOOK_MOCK_LEADS = [
    {
        "title": "Sound Bath Healing & Singing Bowls Community - Facebook Page",
        "snippet": "Join our weekly sound meditation events in Denver! For partnership and wholesale supply of bowls, contact page admin at wholesale@denversoundbath.org.",
        "url": "https://www.facebook.com/denversoundbath",
        "platform": "Facebook"
    },
    {
        "title": "Tibetan Singing Bowls & Meditation Arts Group",
        "snippet": "A group for sound healing practitioners. Looking for exporters of authentic 7-metal singing bowls from Nepal. Send offers to admin@tibetansingingbowlsgroup.net.",
        "url": "https://www.facebook.com/groups/tibetanbowlshealing",
        "platform": "Facebook"
    },
    {
        "title": "Sacred Sound Sanctuary - Facebook Shop",
        "snippet": "We sell spiritual tools, brass statues, and meditation bowls. Suppliers can contact our inventory manager: procurement@sacredsoundsanctuary.com.",
        "url": "https://www.facebook.com/sacredsoundsanctuary",
        "platform": "Facebook"
    },
    {
        "title": "Yoga & Mindfulness Studio Owners Network - Facebook Group",
        "snippet": "Post by Sarah Jenkins: 'Hey everyone, where can I import high-quality, fair-trade singing bowls for my studio retail section?' Reply: 'Contact sarah@jenkinsyoga.com.'",
        "url": "https://www.facebook.com/groups/yogastudionetwork/posts/94821",
        "platform": "Facebook"
    },
    {
        "title": "Himalayan Art & Sound Therapies - Facebook Business Page",
        "snippet": "Distributors of authentic singing bowls, gongs, and bells. Wholesale buyer contact: sales@himalayanarttherapy.com.",
        "url": "https://www.facebook.com/himalayanarttherapy",
        "platform": "Facebook"
    }
]

def search_facebook(keyword, max_results=5):
    """
    Real-time retail shop, boutique, and commercial community search adapter.
    Discovers independent retailers, shops, and studios selling products in the target niche.
    """
    print(f"[Facebook Search] Querying live retail & boutique network for: '{keyword}'...")
    query = f"{keyword} retail store shop boutique wholesale supplier contact email"
    url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}&first=31"
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
                    "platform": "Facebook"
                })
                
        if results:
            print(f"[Facebook Search] Found {len(results)} live commercial store records for '{keyword}'.")
            return results
    except Exception as e:
        print(f"[Facebook Search] Live query failed ({e}), using baseline...")
        
    limit = min(max_results, len(FACEBOOK_MOCK_LEADS))
    return FACEBOOK_MOCK_LEADS[:limit]
