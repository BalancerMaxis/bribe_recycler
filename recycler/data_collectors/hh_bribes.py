import requests
from typing import List, Dict

HH_AURA_URL = "https://api.hiddenhand.finance/proposal/aura"


def fetch_hh_aura_bribs() -> List[Dict]:
    """
    Fetch GET bribes from hidden hand api
    """
    res = requests.get(HH_AURA_URL)
    if not res.ok:
        raise ValueError("Error fetching bribes from hidden hand api")

    response_parsed = res.json()
    if response_parsed["error"]:
        raise ValueError("HH API returned error")
    return response_parsed["data"]
