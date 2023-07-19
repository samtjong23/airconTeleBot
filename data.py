import json
import os
from dotenv import load_dotenv

# Bot retrieves env references here
load_dotenv()

FORM_FIELD_IDS = json.loads(os.getenv("FORM_FIELD_IDS"))
FORM_URL = os.getenv("FORM_URL")
TOKEN = os.getenv("TOKEN")
USER_NAME_MAPPING = json.loads(os.getenv("USER_NAME_MAPPING"))

# Bot stores user sessions here
user_sessions = {}
