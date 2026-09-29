import urllib.request
import re

url = "https://paimana-proj.mospi.gov.in/Home/PublicDashboard"
print(f"Fetching {url}...")
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, timeout=10)
    data = res.read().decode('utf-8', errors='replace')
    print(f"Status: {res.status}, Length: {len(data)}")
    # Find tables, iframes, exports, scripts
    print("Tables:", len(re.findall(r'<table', data)))
    print("Inputs:", len(re.findall(r'<input', data)))
    print("Downloads/Exports:", re.findall(r'href=[\"\']([^\"\']*(?:export|excel|csv|download|pdf)[^\"\']*)[\"\']', data, re.IGNORECASE))
    with open("paimana_PublicDashboard.html", "w", encoding="utf-8") as f:
        f.write(data)
except Exception as e:
    print("Error:", e)
