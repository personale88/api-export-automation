import random

# Realistic simulated LinkedIn leads for Singing Bowls / Sound healing buyers
LINKEDIN_MOCK_LEADS = [
    {
        "title": "David Miller - Founder & CEO at Harmony Sound Imports",
        "snippet": "David Miller's profile: Importing handcrafted sound healing instruments for retailers across Canada. Contact: dmiller@harmonysoundimports.ca.",
        "url": "https://www.linkedin.com/in/david-miller-harmonysounds",
        "platform": "LinkedIn"
    },
    {
        "title": "Elena Rostova - Sourcing Director at Munich Yoga Supplies",
        "snippet": "Elena Rostova is responsible for purchasing wholesale meditation accessories and singing bowls. Sourcing inquiries: elena.rostova@munichyogasupplies.de.",
        "url": "https://www.linkedin.com/in/elena-rostova-yogasourcing",
        "platform": "LinkedIn"
    },
    {
        "title": "Aurore Dubois - Sound Healing Therapist & Spa Coordinator",
        "snippet": "Coordinating holistic wellness products for luxury hotel spas in France. Direct inquiries: a.dubois@spaserenityfrance.fr.",
        "url": "https://www.linkedin.com/in/aurore-dubois-soundspa",
        "platform": "LinkedIn"
    },
    {
        "title": "Marcus Vance - Wholesale Purchaser at Sound Bath Co.",
        "snippet": "Sound Bath Co. is expanding its inventory of Tibetan singing bowls and gongs. Reach out at procurement@soundbathco.com.",
        "url": "https://www.linkedin.com/in/marcus-vance-soundbath",
        "platform": "LinkedIn"
    },
    {
        "title": "Siddharth Mehta - Import Coordinator at Nirvana Crafts Australia",
        "snippet": "Importers of fine hand-hammered singing bowls, bells, and spiritual art. Email: imports@nirvanacraftsau.com.",
        "url": "https://www.linkedin.com/in/siddharth-mehta-nirvanaimports",
        "platform": "LinkedIn"
    }
]

def search_linkedin(keyword, max_results=5):
    """
    Simulated LinkedIn Search Adapter.
    Returns high-quality simulated LinkedIn profiles and posts.
    """
    print(f"[LinkedIn Search] Simulating query: '{keyword}' (ToS Compliant)...")
    # Return a subset of mock leads
    limit = min(max_results, len(LINKEDIN_MOCK_LEADS))
    results = LINKEDIN_MOCK_LEADS[:limit]
    print(f"[LinkedIn Search] Simulated {len(results)} ToS-compliant records.")
    return results
