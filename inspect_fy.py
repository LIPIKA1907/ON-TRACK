import re

with open("paimana_ProjectMonitoring.html", "r", encoding="utf-8") as f:
    text = f.read()

matches = [m.start() for m in re.finditer(r'financialYearDropdown', text)]
for idx in matches:
    print("--- Match ---")
    print(text[max(0, idx-200):min(len(text), idx+400)])
