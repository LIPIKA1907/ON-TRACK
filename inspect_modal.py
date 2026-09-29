import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("paimana_PublicDashboardNew.html", "r", encoding="utf-8") as f:
    text = f.read()

matches = [m.start() for m in re.finditer(r'Project Overview', text)]
for idx in matches:
    print("--- Match ---")
    print(text[max(0, idx-100):min(len(text), idx+1000)])
