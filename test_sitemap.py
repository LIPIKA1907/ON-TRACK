import urllib.request
import re

url = "https://paimana-proj.mospi.gov.in/QuickLink/SiteMap"
print(f"Fetching {url}...")
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, timeout=10)
    data = res.read().decode('utf-8', errors='replace')
    print(f"Status: {res.status}, Length: {len(data)}")
    links = re.findall(r'<a\s+[^>]*href=[\"\']([^\"\']*)[\"\'][^>]*>([\s\S]*?)</a>', data, re.IGNORECASE)
    print("SiteMap Links:")
    for href, text in links:
        clean = re.sub(r'<[^>]+>', '', text).strip()
        print(f"  {clean} -> {href}")
except Exception as e:
    print("Error:", e)
