import re

with open("paimana_PublicDashboardNew.html", "r", encoding="utf-8") as f:
    text = f.read()

# Search for $.ajax or fetch or axios or url: in scripts
ajax_calls = re.findall(r'(?:url\s*:\s*[\'\"]([^\'\"]+)[\'\"]|fetch\([\'\"]([^\'\"]+)[\'\"])', text)
print("PublicDashboardNew Ajax URLs:")
for u in set(filter(None, [a or b for a, b in ajax_calls])):
    print(" ", u)

# Also look for javascript functions or script blocks
scripts = re.findall(r'<script[\s\S]*?</script>', text)
print(f"\nTotal scripts: {len(scripts)}")
for i, s in enumerate(scripts):
    if "ajax" in s.lower() or "get" in s.lower() or "post" in s.lower() or "chart" in s.lower():
        # print first few lines of this script
        lines = [line.strip() for line in s.split('\n') if any(k in line.lower() for k in ['url', 'data:', 'type:', 'datatype', 'post', 'get'])]
        print(f"Script {i} relevant lines:")
        for l in lines[:10]:
            print("   ", l)
