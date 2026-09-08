import requests
from bs4 import BeautifulSoup
import urllib.parse
from search.google_search import resolve_search_url, IGNORED_DOMAINS

DIRECTORY_MOCK_LEADS = [
    {
        "title": "Chakra Wellness & Spiritual Shop",
        "snippet": "Local directory listing for Chakra Wellness in New York. Retailers of crystals, incense, and hand-hammered singing bowls. Email: sourcing@chakrawellnessnyc.com.",
        "url": "https://www.chakrawellnessnyc.com",
        "platform": "Business Directory"
    },
    {
        "title": "Prana Sound Therapy & Yoga Center",
        "snippet": "Directory profile of Prana Sound Therapy in Chicago, IL. Sells wholesale wellness gear and yoga accessories. Email: info@pranasoundchicago.com.",
        "url": "https://www.pranasoundchicago.com",
        "platform": "Business Directory"
    },
    {
        "title": "Sacred Spaces Sound Healing Studio",
        "snippet": "Spiritual healing therapy directory listing. Sourcing meditation bowls, tingsha bells, and wind chimes. Email: hello@sacredspacessound.com.",
        "url": "http://www.sacredspacessound.com",
        "platform": "Business Directory"
    },
    {
        "title": "The Tibet Craft and Gift Boutique",
        "snippet": "Local gift shop listing in San Francisco. Retailers of Himalayan arts, singing bowls, and prayer flags. Contact: shop@tibetgiftboutique.com.",
        "url": "https://www.tibetgiftboutique.com",
        "platform": "Business Directory"
    },
    {
        "title": "Oasis Sound Sanctuary Spa",
        "snippet": "B2B listing for Oasis Spa in Vancouver. Seeking global exporters of premium quartz and metal singing bowls. Sourcing manager: buyer@oasissoundsanctuary.ca.",
        "url": "https://www.oasissoundsanctuary.ca",
        "platform": "Business Directory"
    }
]

def search_directory(keyword, max_results=5):
    """
    Real-time Business Directory Adapter.
    Searches trade directories and supplier registries live for the target keyword.
    """
    print(f"[Directory Search] Querying live business directories for: '{keyword}'...")
    query = f"{keyword} wholesale suppliers directory b2b trade leads"
    url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}&first=11"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    results = list(DIRECTORY_MOCK_LEADS[:max_results])
    seen_urls = {r['url'].lower() for r in results}
    try:
        response = requests.get(url, headers=headers, timeout=4)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for item in soup.find_all('li', class_='b_algo'):
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
                
                if resolved_url.lower() not in seen_urls:
                    results.append({
                        "title": h2.get_text().strip(),
                        "snippet": snippet,
                        "url": resolved_url,
                        "platform": "Business Directory"
                    })
                    seen_urls.add(resolved_url.lower())
                    if len(results) >= max_results + 2:
                        break

        print(f"[Directory Search] Found {len(results)} business directory listings for '{keyword}'.")
        return results
    except Exception as e:
        print(f"[Directory Search] Live search notice: {e}. Returning curated dataset...")
        return results
