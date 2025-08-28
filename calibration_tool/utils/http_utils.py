import requests


def http_get(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.strip().replace('"', '')
    return None


def http_put(url, value):
    return requests.put(url, str(value))
