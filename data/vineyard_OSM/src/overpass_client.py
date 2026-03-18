import requests
import time

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def build_query(lat, lon, radius=50):
    return f"""
    [out:json][timeout:25];
    (
      way(around:{radius},{lat},{lon})["landuse"="vineyard"];
      relation(around:{radius},{lat},{lon})["landuse"="vineyard"];
      way(around:{radius},{lat},{lon})["crop"="grape"];
      relation(around:{radius},{lat},{lon})["crop"="grape"];
      way(around:{radius},{lat},{lon})["produce"="grapes"];
      relation(around:{radius},{lat},{lon})["produce"="grapes"];
    );
    out tags center;
    """


def send_request(query, retries=3):
    for _ in range(retries):
        try:
            response = requests.post(OVERPASS_URL, data=query)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        time.sleep(1)
    return None


def parse_response(data):
    if not data or "elements" not in data or len(data["elements"]) == 0:
        return {"is_vineyard": False}

    tags = data["elements"][0].get("tags", {})

    return {
        "is_vineyard": True,
        "name": tags.get("name"),
        "grape_variety": tags.get("grape_variety"),
        "source": "api"
    }


def query(lat, lon):
    query_str = build_query(lat, lon)
    data = send_request(query_str)
    return parse_response(data)
