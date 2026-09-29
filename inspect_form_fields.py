import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("paimana_PublicDashboardNew.html", "r", encoding="utf-8") as f:
    text = f.read()

m = re.search(r'<form id="myForm"[\s\S]*?</form>', text)
if m:
    form_html = m.group(0)
    print("Form HTML len:", len(form_html))
    inputs = re.findall(r'<input[^>]*>', form_html)
    selects = re.findall(r'<select[^>]*>', form_html)
    print("Inputs in form:")
    for inp in inputs:
        print(" ", inp)
    print("Selects in form:")
    for sel in selects:
        print(" ", sel)
