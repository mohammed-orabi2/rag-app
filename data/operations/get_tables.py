import json
import jwt
import requests
from helper_functions import *
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()

SECRET = os.getenv("API_SECRET")
BASE_URL = os.getenv("BASE_URL")


def generate_token():
    payload = {
        "service": "ai-agent",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=120),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def call_endpoint(endpoint: str):
    token = generate_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}{endpoint}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(f"✅ Data from {endpoint}:")
        return response.json()
    else:
        print(f"❌ Failed {response.status_code}: {response.text}")
        return None


def fetch_and_save_filtered_data(output_path="data/operations/raw/new_tables.json"):
    """
    Fetch data from API endpoints, filter out test data, and save to JSON file.
    """

    print("Fetching data from API endpoints...")
    schools = call_endpoint("/agent/all-schools")
    programs = call_endpoint("/agent/all-programs")
    years = call_endpoint("/agent/all-years")
    intake = call_endpoint("/agent/all-program-intakes")
    specializations = call_endpoint("/agent/all-program-specializations")

    tables = [
        schools["data"],
        programs["data"],
        years["data"],
        intake["data"],
        specializations["data"],
    ]

    save_json_file(output_path, tables)
    print(f"✅ Data saved to {output_path}")


if __name__ == "__main__":
    print("Starting data fetch and save process...")
    fetch_and_save_filtered_data()
    print("Process completed.")
