import urllib.request
import re

urls = [
    "https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew",
    "https://paimana-proj.mospi.gov.in/ProjectMonitoring",
    "https://paimana.mospi.gov.in/",
]

for url in urls:
    print(f"\n================ Fetching {url} ================")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=10)
        data = res.read().decode('utf-8', errors='replace')
        print(f"Status: {res.status}, Length: {len(data)} bytes")
        
        # Look for API calls, endpoints, or data scripts
        api_matches = re.findall(r'[\'\"/](?:api|Report|Data|Get[A-Za-z]+|Export[A-Za-z]+|Download[A-Za-z]+)[^\'\"\s>]*', data)
        print("API/Endpoint mentions:", list(set(api_matches))[:15])
        
        # Links to reports / files
        files = re.findall(r'href=[\"\']([^\"\']+\.(?:pdf|xlsx|xls|csv|json))[\"\']', data, re.IGNORECASE)
        print("File downloads:", list(set(files))[:15])
        
        # Save HTML
        fname = url.split('/')[-1] or "root"
        with open(f"paimana_{fname}.html", "w", encoding="utf-8") as f:
            f.write(data)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
