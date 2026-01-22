import json
import os
import requests
from pathlib import Path
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# PATH SETUP
# ============================================================
BASE_DIR = Path(__file__).resolve().parent  # data_request folder
DATA_DIR = BASE_DIR
DATA_DIR.mkdir(parents=True, exist_ok=True)

RETENTION_FILE = DATA_DIR / "retention_issues.json"
JIRA_FILE = DATA_DIR / "jira_bugs.json"

# ============================================================
# CONFIG - Uses .env or falls back to defaults
# ============================================================

# ---- Retention API ----
RETENTION_URL = "https://api-development.varicontest.com.au/api/v1/v1.1/retention-issues"
# Get tokens from .env file (REQUIRED - set in your .env file)
ACCESS_TOKEN = os.getenv("VARICON_ACCESS_TOKEN", "")
TENANT_ID = os.getenv("VARICON_TENANT_ID", "")
# ---- Jira API ----
JIRA_URL = "https://varicon.atlassian.net/rest/api/3/search/jql"
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

# ============================================================
# UTILITY: SAVE JSON
# ============================================================
def save_json(data, filepath: Path):
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved: {filepath.name}")

# Tenant ID for Retention API


# ============================================================
# 1️⃣ FETCH RETENTION ISSUES
# ============================================================
def fetch_retention():
    headers = {
        "Tenant-Id": TENANT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        print(f"📡 Fetching from: {RETENTION_URL}")
        r = requests.get(RETENTION_URL, headers=headers, timeout=30)
        print(f"   Status: {r.status_code}")

        if r.status_code != 200:
            print(f"   ❌ Error response: {r.text[:500]}")
            return None

        data = r.json()
        save_json(data, RETENTION_FILE)
        return data

    except requests.RequestException as e:
        print(f"❌ Retention API request failed: {e}")
        return None

# ============================================================
# 2️⃣ FETCH JIRA BUGS
# ============================================================
def fetch_jira():
    # JQL query to find bugs
    params = {
        "jql": "project=H2 AND issuetype=Bug AND status != Done",
        "fields": "summary,description,priority,labels,status,created,updated",
        "maxResults": 100,  # Adjust as needed
    }

    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

    try:
        print(f"📡 Fetching from: {JIRA_URL}")
        r = requests.get(
            JIRA_URL,
            params=params,
            auth=auth,
            headers={"Accept": "application/json"},
            timeout=30
        )
        print(f"   Status: {r.status_code}")

        if r.status_code != 200:
            print(f"   ❌ Error response: {r.text[:500]}")
            return None

        data = r.json()
        save_json(data, JIRA_FILE)
        return data

    except requests.RequestException as e:
        print(f"❌ Jira API request failed: {e}")
        return None

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("\n🚀 Starting data fetch...\n")

    retention_data = fetch_retention()
    jira_data = fetch_jira()

    print("\n📊 Fetch Summary")

    if retention_data is not None:
        print(f"Retention records: {len(retention_data)}")
    else:
        print("Retention data: ❌ Not fetched")

    if jira_data is not None:
        print(f"Jira issues: {len(jira_data.get('issues', []))}")
    else:
        print("Jira data: ❌ Not fetched")

    print("\n✅ Script finished\n")
