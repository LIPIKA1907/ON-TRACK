import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("paimana_PublicDashboardNew.html", "r", encoding="utf-8") as f:
    text = f.read()

for term in ['GetTileData', 'GetDashboardTileDataforChart', 'GetSectorList', 'myForm', 'showDataButton']:
    matches = [m.start() for m in re.finditer(term, text)]
    print(f"\n=== Occurrences of {term} ({len(matches)}) ===")
    for idx in matches[:3]:
        print(text[max(0, idx-100):min(len(text), idx+300)])
