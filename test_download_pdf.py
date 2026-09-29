import urllib.request
import urllib.parse

url = "https://paimana-proj.mospi.gov.in/ProjectMonitoring/ViewPdf?id=48&path=Content%5CArchiveReport%5CPerformanceMonitoringReport%5C2024-25%5CCompleteReviewReportApril2024.pdf"
print(f"Requesting {url} ...")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    res = urllib.request.urlopen(req, timeout=20)
    print(f"Status: {res.status}, Type: {res.headers.get('Content-Type')}, Content-Length: {res.headers.get('Content-Length')}")
    # Read first 1MB or check size
    data = res.read(1024 * 1024)
    print(f"Read {len(data)} bytes. Starts with: {data[:20]}")
    with open("sample_report_april2024.pdf", "wb") as f:
        f.write(data)
except Exception as e:
    print(f"Error: {e}")
