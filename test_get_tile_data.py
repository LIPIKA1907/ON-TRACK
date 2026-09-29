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

# 1. Fetch page to set cookies and get token
req = urllib.request.Request("https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew", headers={'User-Agent': 'Mozilla/5.0'})
res = opener.open(req)
html_content = res.read().decode('utf-8', errors='replace')

token_match = re.search(r'name=[\"\']__RequestVerificationToken[\"\']\s+type=[\"\']hidden[\"\']\s+value=[\"\']([^\"\']+)[\"\']', html_content)
token = token_match.group(1) if token_match else None
print(f"Token: {token[:20]}...")

# 2. Get freeze dates
res_freeze = opener.open("https://paimana-proj.mospi.gov.in/Home/GetFreezeDates")
freeze_data = json.loads(res_freeze.read().decode('utf-8'))
last_freeze = freeze_data.get("lastFreeze", "2026-08")
year, month = last_freeze.split("-")
print(f"Using Year: {year}, Month: {month}, MonthYear: {last_freeze}")

post_data = {
    "__RequestVerificationToken": token,
    "Month": month,
    "Year": year,
    "MonthYear": last_freeze,
    "SectorId": "",
    "PROJ_MINISTRY_ID": "",
    "StateId": "",
    "CostRange": "",
}

for cost_val in ["", "0"]:
    post_data["CostRange"] = cost_val
    encoded = urllib.parse.urlencode(post_data).encode('utf-8')
    try:
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
        raw = resp.read().decode('utf-8', errors='replace')
        print(f"\nCostRange='{cost_val}' Response status {resp.status}, length: {len(raw)}")
        data = json.loads(raw)
        print("Success:", data.get("success"))
        if "data" in data and data["data"]:
            d = data["data"]
            print("data keys:", d.keys() if isinstance(d, dict) else type(d))
            if "ProjectsCountTabDetails" in d:
                proj_list = d["ProjectsCountTabDetails"]
                print(f"Found {len(proj_list)} projects in ProjectsCountTabDetails!")
                if proj_list:
                    print("Sample project record 0:")
                    print(json.dumps(proj_list[0], indent=2))
                    # Save sample records to inspect
                    with open("paimana_sample_projects.json", "w", encoding="utf-8") as f:
                        json.dump(proj_list, f, indent=2)
            if "totalProjectsTabData" in d:
                print("totalProjectsTabData:", d["totalProjectsTabData"])
        else:
            print("Preview:", raw[:400])
        break
    except Exception as e:
        print(f"Failed with CostRange='{cost_val}': {e}")
