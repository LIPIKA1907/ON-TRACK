import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("paimana_PublicDashboardNew.html", "r", encoding="utf-8") as f:
    text = f.read()

# Let's extract cards, titles, headers, labels
labels = re.findall(r'<(?:h[1-6]|span|div|p|strong|b)[^>]*class=[\"\']([^\"\']*(?:card|title|tile|header|label|stat|count|value|num|text)[^\"\']*)[\"\'][^>]*>([\s\S]*?)</(?:h[1-6]|span|div|p|strong|b)>', text, re.IGNORECASE)
print(f"Total labeled elements: {len(labels)}")
for cls, content in labels[:30]:
    clean = re.sub(r'<[^>]+>', '', content).strip()
    if clean:
        print(f"  [{cls}] -> {clean}")

# Also look for any static numbers or metrics
numbers = re.findall(r'<h[1-6][^>]*>([\d,\.]+)[\s\S]*?</h[1-6]>', text)
print("\nNumbers in headers:", numbers[:20])

# Check for dropdowns in PublicDashboardNew
dropdowns = re.findall(r'<select[^>]*name=[\"\']([^\"\']*)[\"\'][^>]*>([\s\S]*?)</select>', text)
print("\nDropdowns:")
for name, content in dropdowns:
    opts = re.findall(r'<option[^>]*value=[\"\']([^\"\']*)[\"\'][^>]*>([\s\S]*?)</option>', content)
    print(f"  Select '{name}': {[(val, re.sub(r'<[^>]+>', '', t).strip()) for val, t in opts][:5]}")
