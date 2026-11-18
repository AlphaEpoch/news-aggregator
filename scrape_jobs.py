import datetime
import requests
from bs4 import BeautifulSoup


def scrape_jobs():
  jobs = []
  # Change this URL to your target job board, career page, or RSS feed
  url = "https://news.ycombinator.com/jobs"

  try:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Example parser for Hacker News Jobs (adjust selectors for your target site)
    for item in soup.find_all("tr", class_="athing")[:15]:
      title_tag = item.find("span", class_="titleline")
      if title_tag:
        title = title_tag.text
        link = title_tag.find("a")["href"]
        jobs.append({"title": title, "link": link})
  except Exception as e:
    print(f"Error during scraping: {e}")

  return jobs


def generate_jobs_page(jobs):
  now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
  html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Job Radar</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            background: #0f172a;
            color: #f8fafc;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #334155;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .back-link {{
            color: #38bdf8;
            text-decoration: none;
            font-size: 14px;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
        .job-card {{
            background: #1e293b;
            padding: 16px 20px;
            margin-bottom: 12px;
            border-radius: 8px;
            border: 1px solid #334155;
            transition: border-color 0.2s;
        }}
        .job-card:hover {{
            border-color: #38bdf8;
        }}
        a {{
            color: #38bdf8;
            text-decoration: none;
            font-weight: 500;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .timestamp {{
            color: #94a3b8;
            font-size: 13px;
            margin-top: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🎯 Daily Job Radar</h1>
            <p class="timestamp">Last updated: {now} UTC</p>
        </div>
        <a href="index.html" class="back-link">← Back to Main Page</a>
    </div>
"""

  if not jobs:
    html += '<p style="color: #94a3b8;">No jobs found or scraper selectors need adjustment.</p>'
  else:
    for job in jobs:
      html += f"""
    <div class="job-card">
        <h3><a href="{job["link"]}" target="_blank">{job["title"]}</a></h3>
    </div>
"""

  html += """
</body>
</html>
"""

  with open("jobs.html", "w", encoding="utf-8") as f:
    f.write(html)
  print(f"Generated jobs.html successfully with {len(jobs)} items.")


if __name__ == "__main__":
  jobs = scrape_jobs()
  generate_jobs_page(jobs)
