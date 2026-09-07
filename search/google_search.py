import requests
from bs4 import BeautifulSoup
import urllib.parse
import random
import time

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

def search_google(keyword, max_results=10):
    """
    Search Google for the keyword.
    Tries to scrape but falls back to mock results if blocked/offline.
    """
    print(f"[Google Search] Querying: '{keyword}' (requesting up to {max_results} results)...")
    
    query = f"{keyword} buyer email contact store"
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}&num={max_results * 2}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    results = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if Google blocked us
        if response.status_code != 200:
            print(f"[Google Search] Scraper returned status code {response.status_code}. Using mock fallback database...")
            return MOCK_RESULTS[:max_results]
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for typical Google search result divs
        search_divs = soup.find_all('div', class_='g')
        
        for div in search_divs:
            if len(results) >= max_results:
                break
                
            title_tag = div.find('h3')
            link_tag = div.find('a')
            snippet_tag = div.find('div', class_='VwiC3b') # Google search snippet class
            
            if not snippet_tag:
                # Try fallback snippet classes
                snippet_tag = div.find('div', class_='yDqZFc') or div.find('span', class_='aCOBbc')
                
            if title_tag and link_tag:
                title = title_tag.text
                link = link_tag.get('href', '')
                snippet = snippet_tag.text if snippet_tag else ""
                
                if link.startswith('http'):
                    results.append({
                        "title": title,
                        "snippet": snippet,
                        "url": link,
                        "platform": "Google"
                    })
                    
        # If we got no results, Google probably served a CAPTCHA or modified structure
        if not results:
            print("[Google Search] No results parsed from scraper. Using mock fallback database...")
            return MOCK_RESULTS[:max_results]
            
        print(f"[Google Search] Successfully scraped {len(results)} results from Google.")
        return results
        
    except Exception as e:
        print(f"[Google Search] Scraper failed with error: {e}. Using mock fallback database...")
        return MOCK_RESULTS[:max_results]
