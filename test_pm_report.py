import urllib.request
import json
import urllib.parse

base_url = "https://paimana-proj.mospi.gov.in"

# Let's test different combinations of fyear and month
test_params = [
    {"fyear": "2024-25", "month": "4"},
    {"fyear": "2024-25", "month": "0"},
    {"fyear": "2023-24", "month": "3"},
    {"fyear": "2025-26", "month": "1"},
]

for p in test_params:
    qs = urllib.parse.urlencode(p)
    url = f"{base_url}/ProjectMonitoring/Report?{qs}"
    print(f"\nCalling {url} ...")
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })
        res = urllib.request.urlopen(req, timeout=15)
        print(f"Status: {res.status}, Type: {res.headers.get('Content-Type')}")
        data = res.read().decode('utf-8', errors='replace')
        print(f"Data length: {len(data)}")
        try:
            parsed = json.loads(data)
            print("Parsed keys:", parsed.keys() if isinstance(parsed, dict) else f"list len {len(parsed)}")
            if isinstance(parsed, dict) and 'html' in parsed:
                html_snippet = parsed['html']
                print("HTML length:", len(html_snippet))
                # Save HTML snippet to check table structure
                with open(f"pm_report_{p['fyear']}_{p['month']}.html", "w", encoding="utf-8") as f:
                    f.write(html_snippet)
                print(f"Saved pm_report_{p['fyear']}_{p['month']}.html. Preview:\n{html_snippet[:500]}")
            else:
                print("Preview:", str(parsed)[:300])
        except Exception as e:
            print("Raw preview:", data[:300])
            print("Error parsing json:", e)
    except Exception as e:
        print(f"Request error: {e}")
