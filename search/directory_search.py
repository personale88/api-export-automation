import random

# Realistic simulated business directory listings
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
    Simulated Business Directory Adapter.
    Returns simulated business listings from B2B/local directories.
    """
    print(f"[Directory Search] Querying directories for keyword: '{keyword}'...")
    limit = min(max_results, len(DIRECTORY_MOCK_LEADS))
    results = DIRECTORY_MOCK_LEADS[:limit]
    print(f"[Directory Search] Returned {len(results)} business directory listings.")
    return results
