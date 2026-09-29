import re
import html

with open("paimana_reportpage.html", "r", encoding="utf-8") as f:
    text = f.read()

print(f"Total length: {len(text)} bytes")

# Find forms, buttons, inputs, tables
forms = re.findall(r'<form[\s\S]*?</form>', text, re.IGNORECASE)
print(f"Forms found: {len(forms)}")
for i, form in enumerate(forms):
    print(f"--- Form {i+1} ---")
    action = re.search(r'action=[\"\']([^\"\']*)[\"\']', form)
    method = re.search(r'method=[\"\']([^\"\']*)[\"\']', form)
    print(f"Action: {action.group(1) if action else 'none'}, Method: {method.group(1) if method else 'none'}")
    inputs = re.findall(r'<input[\s\S]*?>', form, re.IGNORECASE)
    print(f"Inputs: {len(inputs)}")
    for inp in inputs:
        print("  ", inp)
    selects = re.findall(r'<select[\s\S]*?</select>', form, re.IGNORECASE)
    for sel in selects:
        name = re.search(r'name=[\"\']([^\"\']*)[\"\']', sel)
        options = re.findall(r'<option[^>]*>([\s\S]*?)</option>', sel)
        print(f"  Select {name.group(1) if name else 'unnamed'}: {[o.strip() for o in options][:5]}")

# Links
links = re.findall(r'<a\s+[^>]*href=[\"\']([^\"\']*)[\"\'][^>]*>([\s\S]*?)</a>', text, re.IGNORECASE)
print(f"\nTotal Links: {len(links)}")
for href, label in links:
    clean_label = re.sub(r'<[^>]+>', '', label).strip()
    if any(k in href.lower() or k in clean_label.lower() for k in ['report', 'download', 'pdf', 'excel', 'xlsx', 'csv', 'data', 'doc', 'archive', 'paimana']):
        print(f"  {clean_label} -> {href}")

# Check tables or headers
tables = re.findall(r'<table[\s\S]*?</table>', text, re.IGNORECASE)
print(f"\nTotal Tables: {len(tables)}")
for i, t in enumerate(tables):
    headers = re.findall(r'<th[^>]*>([\s\S]*?)</th>', t, re.IGNORECASE)
    print(f"Table {i+1} headers: {[re.sub(r'<[^>]+>', '', h).strip() for h in headers]}")
