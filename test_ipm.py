import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://ipm.mospi.gov.in/"
print(f"Fetching {url}...")
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, context=ctx, timeout=10)
    data = res.read().decode('utf-8', errors='replace')
    print(f"Status: {res.status}, Length: {len(data)}")
    links = re.findall(r'<a\s+[^>]*href=[\"\']([^\"\']*)[\"\'][^>]*>([\s\S]*?)</a>', data, re.IGNORECASE)
    print("Interesting links:")
    for href, text in links:
        clean = re.sub(r'<[^>]+>', '', text).strip()
        if any(k in href.lower() or k in clean.lower() for k in ['flash', 'report', 'project', 'download', 'pdf', 'excel', 'data', 'paimana']):
            print(f"  {clean} -> {href}")
except Exception as e:
    print("Error:", e)
