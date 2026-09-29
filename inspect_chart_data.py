import sys
import urllib.request
import urllib.parse
import http.cookiejar
import re
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

req = urllib.request.Request("https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew", headers={'User-Agent': 'Mozilla/5.0'})
res = opener.open(req)
html_content = res.read().decode('utf-8', errors='replace')

token_match = re.search(r'name=[\"\']__RequestVerificationToken[\"\']\s+type=[\"\']hidden[\"\']\s+value=[\"\']([^\"\']+)[\"\']', html_content)
token = token_match.group(1) if token_match else None

# Let's test with month 8, year 2026, or month 4, year 2024 or other dates
for year, month in [("2026", "8"), ("2025", "12"), ("2024", "4"), ("2023", "12")]:
    post_data = {
        "__RequestVerificationToken": token,
        "Month": month,
        "Year": year,
        "SectorId": "0",
        "StateId": "0",
        "CostFilter": "0",
    }
    encoded_data = urllib.parse.urlencode(post_data).encode('utf-8')
    try:
        post_req = urllib.request.Request(
            "https://paimana-proj.mospi.gov.in/Home/GetDashboardTileDataforChart",
            data=encoded_data,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest'
            }
        )
        resp = opener.open(post_req)
        raw = resp.read().decode('utf-8', errors='replace')
        data = json.loads(raw)
        print(f"\n--- Year {year}, Month {month} ---")
        if data.get("success"):
            d = data.get("data", {})
            print("Non-zero fields:")
            for k, v in d.items():
                if v not in (0, 0.0, None, "", [], {}):
                    print(f"  {k}: {str(v)[:100]}")
    except Exception as e:
        print(f"Error {year}-{month}: {e}")
