import re

with open("paimana_ProjectMonitoring.html", "r", encoding="utf-8") as f:
    text = f.read()

# Find financialYearDropdown and financialMonthDropdown
selects = re.findall(r'<select[^>]*id=[\"\'](financialYearDropdown|financialMonthDropdown)[\"\'][^>]*>([\s\S]*?)</select>', text)
for sel_id, content in selects:
    options = re.findall(r'<option\s+value=[\"\']([^\"\']*)[\"\'][^>]*>([\s\S]*?)</option>', content)
    print(f"Select {sel_id}:")
    for val, text_val in options[:10]:
        print(f"  val='{val}' text='{text_val.strip()}'")

# Also find any other selects or table containers
print("Table container in PM:")
tbl = re.findall(r'<div[^>]*id=[\"\']tbl[\"\'][^>]*>([\s\S]*?)</div>', text)
if tbl:
    print(tbl[0][:500])
