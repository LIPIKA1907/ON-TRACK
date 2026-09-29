import urllib.request
import json

base_url = "https://paimana-proj.mospi.gov.in"

endpoints = [
    ("/ProjectMonitoring/GetFinancialYearList", "GET", None),
    ("/Home/GetFreezeDates", "GET", None),
    ("/Home/GetSectorList", "GET", None),
    ("/Home/GetTileData", "GET", None),
]

for ep, method, payload in endpoints:
    url = base_url + ep
    print(f"\nCalling {url} ...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        res = urllib.request.urlopen(req, timeout=10)
        content_type = res.headers.get('Content-Type')
        data = res.read().decode('utf-8', errors='replace')
        print(f"Status: {res.status}, Type: {content_type}, Length: {len(data)}")
        try:
            parsed = json.loads(data)
            print("Parsed JSON preview:", str(parsed)[:300])
        except Exception:
            print("Raw text preview:", data[:300])
    except Exception as e:
        print(f"Error: {e}")
