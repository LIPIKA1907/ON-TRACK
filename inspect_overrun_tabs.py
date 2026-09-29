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

post_data = {
    "__RequestVerificationToken": token,
    "Month": "08",
    "Year": "2026",
    "MonthYear": "2026-08",
    "SectorId": "",
    "PROJ_MINISTRY_ID": "",
    "StateId": "",
    "CostRange": "",
}
encoded = urllib.parse.urlencode(post_data).encode('utf-8')
post_req = urllib.request.Request(
    "https://paimana-proj.mospi.gov.in/Home/GetTileData",
    data=encoded,
    headers={
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew'
    }
)
resp = opener.open(post_req)
data = json.loads(resp.read().decode('utf-8'))
d = data.get("data", {})

time_overrun = d.get("TimeOverrunTabDetails")
cost_overrun = d.get("CostOverrunTabDetails")

print(f"TimeOverrunTabDetails count: {len(time_overrun) if time_overrun else 0}")
if time_overrun:
    print("Sample TimeOverrunTabDetails[0]:", json.dumps(time_overrun[0], indent=2))

print(f"CostOverrunTabDetails count: {len(cost_overrun) if cost_overrun else 0}")
if cost_overrun:
    print("Sample CostOverrunTabDetails[0]:", json.dumps(cost_overrun[0], indent=2))

# Save the full extracted dataset
with open("paimana_full_extract.json", "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": "2026-08",
        "totalProjects": len(d.get("ProjectsCountTabDetails", [])),
        "projects": d.get("ProjectsCountTabDetails", []),
        "timeOverrunProjects": time_overrun,
        "costOverrunProjects": cost_overrun,
        "summary": d.get("totalProjectsTabData", [])
    }, f, indent=2)
print("Saved paimana_full_extract.json successfully!")
