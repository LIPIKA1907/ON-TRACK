import json
import pandas as pd

with open("paimana_sample_projects.json", "r", encoding="utf-8") as f:
    projects = json.load(f)

df = pd.DataFrame(projects)

print(f"Total Records: {len(df)}")
print("\nColumns and non-null counts:")
for col in df.columns:
    non_null = df[col].notna().sum()
    sample_vals = df[col].dropna().unique()[:3]
    print(f"  {col:25} | Non-null: {non_null:4}/{len(df)} | Type: {df[col].dtype} | Sample: {list(sample_vals)}")

print("\nNumeric column summary:")
num_cols = ["OriginalCost", "RevisedCost", "Expenditure", "PhysicalProgress", "DELAYED_TIME", "COST_OVERRUN_PERC", "COST_OVERRUN"]
for c in num_cols:
    numeric_s = pd.to_numeric(df[c], errors="coerce")
    print(f"  {c:20} -> Min: {numeric_s.min()}, Max: {numeric_s.max()}, Mean: {numeric_s.mean():.2f}, Nulls: {numeric_s.isna().sum()}")

print("\nTop Sectors:")
print(df["SectorName"].value_counts().head(10))

print("\nTop Line Ministries:")
print(df["LineMinistry"].value_counts().head(10))

print("\nTop Implementing Agencies (COMPANYNAME):")
print(df["COMPANYNAME"].value_counts().head(10))
