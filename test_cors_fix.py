"""Full CORS & Endpoint Verification for OnTrack AI."""
import urllib.request
import json
import pandas as pd

PORT = 8001
ORIGIN = "http://localhost:5173"


def test(label, url, method="GET", body=None, headers=None):
    hdrs = {"Origin": ORIGIN}
    if headers:
        hdrs.update(headers)
    data = body.encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in hdrs.items():
        req.add_header(k, v)
    try:
        resp = urllib.request.urlopen(req)
        cors = resp.headers.get("Access-Control-Allow-Origin", "MISSING")
        bdy = json.loads(resp.read().decode("utf-8"))
        success = bdy.get("success", "N/A")
        print(f"  [{label}] {resp.getcode()} OK | CORS: {cors} | success={success}")
        return bdy
    except Exception as e:
        cors = "N/A"
        if hasattr(e, "headers"):
            cors = e.headers.get("Access-Control-Allow-Origin", "MISSING")
        print(f"  [{label}] ERROR {e} | CORS: {cors}")
        return None


print("=" * 60)
print("OnTrack AI CORS & Endpoint Verification")
print("=" * 60)

# 1. GET /health
print()
print("1. GET /health")
h = test("health", f"http://127.0.0.1:{PORT}/health")
if h:
    print(f"     PAIMANA status: {h.get('paimana_status')} | available: {h.get('paimana_available')}")

# 2. OPTIONS /explain preflight
print()
print("2. OPTIONS /explain (preflight)")
preq = urllib.request.Request(f"http://127.0.0.1:{PORT}/explain", method="OPTIONS")
preq.add_header("Origin", ORIGIN)
preq.add_header("Access-Control-Request-Method", "POST")
preq.add_header("Access-Control-Request-Headers", "content-type")
try:
    resp = urllib.request.urlopen(preq)
    print(f"  [preflight] {resp.getcode()} OK")
    print(f"     CORS Origin: {resp.headers.get('Access-Control-Allow-Origin')}")
    print(f"     CORS Methods: {resp.headers.get('Access-Control-Allow-Methods')}")
    print(f"     CORS Headers: {resp.headers.get('Access-Control-Allow-Headers')}")
except Exception as e:
    print(f"  [preflight] ERROR: {e}")

# 3. POST /explain with real PAIMANA project
print()
print("3. POST /explain (real PAIMANA project)")
df = pd.read_csv("data/paimana/paimana_normalized.csv")
project = {k: (None if pd.isna(v) else v) for k, v in df.iloc[0].to_dict().items()}
body = json.dumps({"project": project})
exp = test("explain", f"http://127.0.0.1:{PORT}/explain", "POST", body, {"Content-Type": "application/json"})
if exp and exp.get("result"):
    r = exp["result"]
    print(f"     Project: {r.get('project_id')} | Risk: {r.get('risk_level')} ({r.get('overall_risk_score')})")

# 4. POST /predict
print()
print("4. POST /predict")
test("predict", f"http://127.0.0.1:{PORT}/predict", "POST", body, {"Content-Type": "application/json"})

# 5. POST /benchmark
print()
print("5. POST /benchmark")
test("benchmark", f"http://127.0.0.1:{PORT}/benchmark", "POST", body, {"Content-Type": "application/json"})

# 6. POST /recommendations
print()
print("6. POST /recommendations")
test("recommendations", f"http://127.0.0.1:{PORT}/recommendations", "POST", body, {"Content-Type": "application/json"})

# 7. POST /early-warning
print()
print("7. POST /early-warning")
test("early-warning", f"http://127.0.0.1:{PORT}/early-warning", "POST", body, {"Content-Type": "application/json"})

print()
print("=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
