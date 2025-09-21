import os
import json
import tempfile
from dotenv import load_dotenv
from contextlib import contextmanager
load_dotenv()  # load variables from .env

@contextmanager
def service_account_credentials():
    print("Setting up GCP credentials...")
    if "gcp_cred_path" not in globals():
        # Load JSON from env
        gcp_info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

    # Write to a temporary JSON file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as tmpfile:
        json.dump(gcp_info, tmpfile)
        tmpfile.flush()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmpfile.name
        print(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        gcp_cred_path = tmpfile.name
        try:
            yield tmpfile.name
        finally:
            print("Google creds setup successfully!")
    
