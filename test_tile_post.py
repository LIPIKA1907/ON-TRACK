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

# 1. Fetch dashboard page
req = urllib.request.Request("https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew", headers={'User-Agent': 'Mozilla/5.0'})
res = opener.open(req)
html_content = res.read().decode('utf-8', errors='replace')

# Extract token
token_match = re.search(r'name=[\"\']__RequestVerificationToken[\"\']\s+type=[\"\']hidden[\"\']\s+value=[\"\']([^\"\']+)[\"\']', html_content)
token = token_match.group(1) if token_match else None
print(f"Verification token: {token[:25]}..." if token else "No token found")

# Test GetFreezeDates
res_freeze = opener.open("https://paimana-proj.mospi.gov.in/Home/GetFreezeDates")
freeze_data = json.loads(res_freeze.read().decode('utf-8'))
print("Freeze dates:", freeze_data)

# Test GetTileData POST
# Form fields: Month, Year, SectorId, MinistryDropdown, etc.
# From freeze_data, lastFreeze is e.g. "2026-08" -> Year=2026, Month=8
last_freeze = freeze_data.get("lastFreeze", "2024-03")
parts = last_freeze.split("-")
post_data = {
    "__RequestVerificationToken": token,
    "Month": parts[1] if len(parts) > 1 else "8",
    "Year": parts[0] if len(parts) > 0 else "2026",
    "SectorId": "0",
    "StateId": "0",
    "CostFilter": "0",
}
encoded_data = urllib.parse.urlencode(post_data).encode('utf-8')

for endpoint in ["/Home/GetTileData", "/Home/GetDashboardTileDataforChart"]:
    try:
        post_req = urllib.request.Request(
            f"https://paimana-proj.mospi.gov.in{endpoint}",
            data=encoded_data,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest'
            }
        )
        resp = opener.open(post_req)
        raw = resp.read().decode('utf-8', errors='replace')
        print(f"\n{endpoint} response (status {resp.status}, len {len(raw)}):")
        try:
            parsed = json.loads(raw)
            print(json.dumps(parsed, indent=2)[:800])
        except Exception:
            print(raw[:500])
    except Exception as e:
        print(f"Error calling {endpoint}: {e}")
