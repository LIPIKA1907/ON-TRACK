import json
from datetime import datetime

with open("paimana_sample_projects.json", "r", encoding="utf-8") as f:
    projects = json.load(f)

def parse_date(d_str):
    if not d_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(d_str.strip(), fmt)
        except Exception:
            pass
    return None

valid_planned_duration = 0
valid_time_overrun = 0
valid_cost_overrun = 0
cost_overrun_positive = 0
time_overrun_positive = 0

delays_months = []
cost_overruns_pct = []

for p in projects:
    s_date = parse_date(p.get("SanctionDate"))
    end_date = parse_date(p.get("OriginalEndDate"))
    rev_date = parse_date(p.get("RevisedDate"))
    
    orig_cost = None
    rev_cost = None
    try:
        if p.get("OriginalCost") is not None:
            orig_cost = float(p.get("OriginalCost"))
    except: pass
    try:
        if p.get("RevisedCost") is not None:
            rev_cost = float(p.get("RevisedCost"))
    except: pass
    
    if s_date and end_date:
        planned_months = (end_date.year - s_date.year) * 12 + (end_date.month - s_date.month)
        if planned_months > 0:
            valid_planned_duration += 1
            
    if end_date and rev_date:
        delay_months = (rev_date.year - end_date.year) * 12 + (rev_date.month - end_date.month)
        valid_time_overrun += 1
        delays_months.append(delay_months)
        if delay_months > 0:
            time_overrun_positive += 1
            
    if orig_cost and rev_cost and orig_cost > 0:
        cost_esc = ((rev_cost - orig_cost) / orig_cost) * 100.0
        valid_cost_overrun += 1
        cost_overruns_pct.append(cost_esc)
        if cost_esc > 0.01:
            cost_overrun_positive += 1

print(f"Total projects: {len(projects)}")
print(f"Valid planned duration derived: {valid_planned_duration}/{len(projects)} ({valid_planned_duration/len(projects)*100:.1f}%)")
print(f"Valid time overrun derived: {valid_time_overrun}/{len(projects)} ({valid_time_overrun/len(projects)*100:.1f}%)")
print(f"Projects with positive time delay (RevisedDate > OriginalEndDate): {time_overrun_positive} ({time_overrun_positive/len(projects)*100:.1f}%)")
if delays_months:
    print(f"  Delay months -> Min: {min(delays_months)}, Max: {max(delays_months)}, Avg: {sum(delays_months)/len(delays_months):.1f}")
print(f"Valid cost overrun derived: {valid_cost_overrun}/{len(projects)} ({valid_cost_overrun/len(projects)*100:.1f}%)")
print(f"Projects with positive cost overrun (RevisedCost > OriginalCost): {cost_overrun_positive} ({cost_overrun_positive/len(projects)*100:.1f}%)")
if cost_overruns_pct:
    print(f"  Cost overrun % -> Min: {min(cost_overruns_pct):.1f}%, Max: {max(cost_overruns_pct):.1f}%, Avg: {sum(cost_overruns_pct)/len(cost_overruns_pct):.1f}%")
