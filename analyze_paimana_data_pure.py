import json
from collections import Counter
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("paimana_sample_projects.json", "r", encoding="utf-8") as f:
    projects = json.load(f)

total = len(projects)
print(f"Total Projects Extracted: {total}")

# Gather all keys
keys = set()
for p in projects:
    keys.update(p.keys())

print(f"\nAll Field Names ({len(keys)} fields):")
field_stats = {}
for k in sorted(keys):
    non_null_count = 0
    types = Counter()
    samples = []
    for p in projects:
        val = p.get(k)
        if val is not None and val != "":
            non_null_count += 1
            types[type(val).__name__] += 1
            if len(samples) < 3 and val not in samples:
                samples.append(val)
    field_stats[k] = {
        "non_null": non_null_count,
        "types": dict(types),
        "samples": samples
    }
    pct = (non_null_count / total) * 100
    print(f"  {k:25} | Present: {non_null_count:4}/{total} ({pct:5.1f}%) | Types: {dict(types)} | Samples: {samples}")

# Top Sectors
print("\nTop Sectors in Real PAIMANA Data:")
sectors = Counter(p.get("SectorName") for p in projects)
for s, c in sectors.most_common(10):
    print(f"  {s}: {c} projects ({c/total*100:.1f}%)")

# Top Ministries
print("\nTop Ministries in Real PAIMANA Data:")
ministries = Counter(p.get("LineMinistry") for p in projects)
for m, c in ministries.most_common(10):
    print(f"  {m}: {c} projects ({c/total*100:.1f}%)")

# Top Agencies
print("\nTop Implementing Agencies (COMPANYNAME):")
agencies = Counter(p.get("COMPANYNAME") for p in projects)
for a, c in agencies.most_common(10):
    print(f"  {a}: {c} projects ({c/total*100:.1f}%)")

# Numeric fields analysis
print("\nNumeric fields analysis:")
num_fields = ["OriginalCost", "RevisedCost", "Expenditure", "PhysicalProgress", "DELAYED_TIME", "COST_OVERRUN_PERC", "COST_OVERRUN"]
for fld in num_fields:
    vals = []
    for p in projects:
        v = p.get(fld)
        if v is not None and v != "":
            try:
                vals.append(float(v))
            except ValueError:
                pass
    if vals:
        print(f"  {fld:20} -> Valid: {len(vals):4} | Min: {min(vals):10.2f} | Max: {max(vals):10.2f} | Avg: {sum(vals)/len(vals):10.2f}")
    else:
        print(f"  {fld:20} -> No valid numeric values")

# Date fields analysis
print("\nDate fields presence:")
date_fields = ["SanctionDate", "CreationDate", "StartDate", "OriginalEndDate", "RevisedDate"]
for df in date_fields:
    non_empty = sum(1 for p in projects if p.get(df) not in (None, ""))
    print(f"  {df:20} -> Present in {non_empty:4}/{total} projects ({non_empty/total*100:.1f}%)")
