import requests
import os


def get_salesforce_token():
    url = os.environ["SF_AUTH_URL"]
    data = {
        "grant_type": "password",
        "client_id": os.environ["SF_CLIENT_ID"],
        "client_secret": os.environ["SF_CLIENT_SECRET"],
        "username": os.environ["SF_USERNAME"],
        "password": os.environ["SF_PASSWORD"],
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"], resp.json()["instance_url"]


def fetch_customers():
    token, instance_url = get_salesforce_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{instance_url}/services/data/v52.0/query"
    params = {"q": "SELECT Id, Name, Email FROM Contact"}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()["records"]
