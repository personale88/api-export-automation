import os
import json
from dotenv import load_dotenv

# Load env variables from .env file if it exists
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SETTINGS_PATH = os.path.join(DATA_DIR, 'settings.json')

# Create necessary directories on import
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'assets'), exist_ok=True)

DEFAULT_SETTINGS = {
    "GMAIL_EMAIL": os.getenv("GMAIL_EMAIL", ""),
    "GMAIL_APP_PASSWORD": os.getenv("GMAIL_APP_PASSWORD", ""),
    "SMTP_HOST": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT", "465")),
    "DAILY_SEND_LIMIT": int(os.getenv("DAILY_SEND_LIMIT", "80")),
    "SEND_DELAY": int(os.getenv("SEND_DELAY", "2")),
    "SEARCH_KEYWORD": os.getenv("SEARCH_KEYWORD", "Singing Bowls"),
    "PHYSICAL_ADDRESS": os.getenv("PHYSICAL_ADDRESS", "Singing Bowls Export Co., 123 Healing Sound Way, Kathmandu, Nepal"),
    "DEFAULT_SUBJECT": "Direct Importing of Premium Singing Bowls for {company_name}",
    "DEFAULT_BODY": (
        "Dear {buyer_name},\n\n"
        "I hope this email finds you well.\n\n"
        "We discovered your business, {company_name}, via {source_platform} and noticed your interest in high-quality wellness/sound-healing products. We are a direct exporter of handcrafted Singing Bowls from Nepal.\n\n"
        "We have attached our latest product catalog and wholesale price list for your review. We offer direct-to-port shipping, custom packaging, and certified fair-trade quality.\n\n"
        "Please let us know if you have any questions or if you would like to request physical samples.\n\n"
        "Best regards,\n\n"
        "Singing Bowls Export Team\n"
    ),
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "")
}

class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance.load()
        return cls._instance

    def load(self):
        self.BASE_DIR = BASE_DIR
        self.DATA_DIR = DATA_DIR
        self.settings = DEFAULT_SETTINGS.copy()
        
        # Load from settings.json if it exists
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, 'r') as f:
                    saved = json.load(f)
                    self.settings.update(saved)
            except Exception as e:
                print(f"Error loading settings.json: {e}")
        
        # Ensure fallback from environment if values are blank in settings.json
        if not self.settings.get("GMAIL_EMAIL"):
            self.settings["GMAIL_EMAIL"] = os.getenv("GMAIL_EMAIL", "")
        if not self.settings.get("GMAIL_APP_PASSWORD"):
            self.settings["GMAIL_APP_PASSWORD"] = os.getenv("GMAIL_APP_PASSWORD", "")
            
        # Clean app password of spaces
        if self.settings.get("GMAIL_APP_PASSWORD"):
            self.settings["GMAIL_APP_PASSWORD"] = str(self.settings["GMAIL_APP_PASSWORD"]).replace(" ", "")
            
        # Ensure types are correct
        self.settings["DAILY_SEND_LIMIT"] = int(self.settings.get("DAILY_SEND_LIMIT", 80))
        self.settings["SEND_DELAY"] = int(self.settings.get("SEND_DELAY", 2))
        self.settings["SMTP_PORT"] = int(self.settings.get("SMTP_PORT", 465))
        
        # Keep environmental overrides for API key if missing from file
        if not self.settings.get("GEMINI_API_KEY"):
            self.settings["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

    def save(self):
        try:
            with open(SETTINGS_PATH, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings.json: {e}")

    def get(self, key, default=None):
        val = self.settings.get(key)
        if val is not None and val != "":
            return val
        if default is not None:
            return default
        return DEFAULT_SETTINGS.get(key, default)

    def update(self, new_settings):
        # Update internally
        for k, v in new_settings.items():
            if k in DEFAULT_SETTINGS:
                # Type conversions & cleanup
                if k in ("DAILY_SEND_LIMIT", "SEND_DELAY", "SMTP_PORT"):
                    v = int(v)
                elif k == "GMAIL_APP_PASSWORD":
                    v = str(v).replace(" ", "")
                self.settings[k] = v
        self.save()

# Singleton configuration instance
config = AppConfig()
