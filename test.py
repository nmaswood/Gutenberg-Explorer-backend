import requests

url = "http://127.0.0.1:8000/analyze-book/123"

with requests.get(url, stream=True) as r:
    for chunk in r.iter_content(1024):  # or, for line in r.iter_lines():
        print(chunk)