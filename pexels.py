import json
import requests
import os

API_KEY = os.getenv("PEXELS_API_KEY")

def top_pexels_result(query):
    base_url = "https://api.pexels.com/v1/search"

    # Build parameters
    params = {
        'query': query,
        'per_page': 1,
    }

    # Set up headers
    headers = {
        'Authorization': API_KEY
    }

    response = requests.get(base_url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["photos"][0]