import random

# Realistic simulated Facebook leads for Singing Bowls / Sound healing buyers
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
    Simulated Facebook Search Adapter.
    Returns high-quality simulated Facebook posts and pages.
    """
    print(f"[Facebook Search] Simulating query: '{keyword}' (ToS Compliant)...")
    # Return a subset of mock leads
    limit = min(max_results, len(FACEBOOK_MOCK_LEADS))
    results = FACEBOOK_MOCK_LEADS[:limit]
    print(f"[Facebook Search] Simulated {len(results)} ToS-compliant records.")
    return results
