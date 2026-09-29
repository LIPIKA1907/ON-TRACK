import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("paimana_PublicDashboardNew.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("ProjectsCountTabDetails")
if idx != -1:
    print(text[max(0, idx-1500):idx])
