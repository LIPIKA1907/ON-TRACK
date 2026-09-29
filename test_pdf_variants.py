import urllib.request
import urllib.parse

paths = [
    "https://paimana-proj.mospi.gov.in/Content/ArchiveReport/PerformanceMonitoringReport/2024-25/CompleteReviewReportApril2024.pdf",
    "https://paimana-proj.mospi.gov.in/ProjectMonitoring/ViewPdf?id=48&path=Content/ArchiveReport/PerformanceMonitoringReport/2024-25/CompleteReviewReportApril2024.pdf",
    "https://paimana-proj.mospi.gov.in/ProjectMonitoring/ViewPdf?id=48",
]

for url in paths:
    print(f"\nRequesting {url} ...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=10)
        print(f"Status: {res.status}, Type: {res.headers.get('Content-Type')}, Length: {res.headers.get('Content-Length')}")
        sample = res.read(100)
        print(f"Starts with: {sample[:20]}")
    except Exception as e:
        print(f"Error: {e}")
