import os
import json
from google.oauth2 import service_account

def get_credentials():
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        return None
    service_account_info = json.loads(service_account_json)
    return service_account.Credentials.from_service_account_info(service_account_info)