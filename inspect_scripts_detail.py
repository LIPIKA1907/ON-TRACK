import re

with open("paimana_PublicDashboardNew.html", "r", encoding="utf-8") as f:
    text = f.read()

scripts = re.findall(r'<script[\s\S]*?</script>', text)
print("=== PublicDashboardNew Script 15 ===")
if len(scripts) > 15:
    print(scripts[15][:3000])

with open("paimana_ProjectMonitoring.html", "r", encoding="utf-8") as f:
    text_pm = f.read()

scripts_pm = re.findall(r'<script[\s\S]*?</script>', text_pm)
print("\n=== ProjectMonitoring Scripts ===")
for i, s in enumerate(scripts_pm):
    if "ajax" in s.lower() or "report" in s.lower() or "get" in s.lower() or "post" in s.lower():
        print(f"PM Script {i}:")
        print(s[:1500])
