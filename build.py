import datetime
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET
import urllib.request
import random
import email.utils
import re
import concurrent.futures

# Matrix Quote Engine
QUOTES = [
    "\"You take the red pill, you stay in Wonderland, and I show you how deep the rabbit hole goes.\" — Morpheus",
    "\"There is a difference between knowing the path and walking the path.\" — Morpheus",
    "\"The Matrix is a system, Neo. That system is our enemy.\" — Morpheus",
    "\"What's really going to bake your noodle later on is, would you still have broken it if I hadn't said anything?\" — The Oracle",
    "\"Ever have that feeling where you're not sure if you're awake or dreaming?\" — Neo",
    "\"I'm trying to free your mind, Neo. But I can only show you the door. You're the one that has to walk through it.\" — Morpheus",
    "\"Choice is an illusion created between those with power and those without.\" — The Merovingian",
    "\"It is the question that drives us, Neo. It's the question that brought you here.\" — Trinity",
    "\"The body cannot live without the mind.\" — Morpheus",
    "\"Free your mind.\" — Morpheus"
]
selected_quote = random.choice(QUOTES)

target_timezone = ZoneInfo("America/New_York")
now_eastern = datetime.datetime.now(target_timezone)

def compute_time_ago(article_dt, current_dt):
    diff = current_dt - article_dt
    seconds = diff.total_seconds()
    if seconds < 0: return "just now"
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)
    if days > 0: return f"{days}d ago"
    elif hours > 0: return f"{hours}h ago"
    elif minutes > 0: return f"{minutes}m ago"
    else: return "just now"

def strip_to_clean_domain(channel_title, feed_url):
    cleaned = channel_title.lower()
    cleaned = re.sub(r'(\brss\b|\bfeed\b|\bofficial\b|\bnews\b|\bblog\b)', '', cleaned)
    cleaned = re.sub(r'[^a-z0-9\s\.]', '', cleaned).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    if not cleaned or len(cleaned) < 3 or cleaned in ['unknown source', 'home']:
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', feed_url)
        if domain_match: return domain_match.group(1).lower()
        return "unknown"
        
    if " " in cleaned:
        if "stateless society" in cleaned or "c4ss" in cleaned: return "c4ss.org"
        if "crimethinc" in cleaned: return "crimethinc.com"
        if "one championship" in cleaned or "one fc" in cleaned: return "onefc.com"
        return cleaned.replace(" ", ".")
    return cleaned

# Single feed worker function for concurrent fetching execution
def fetch_single_feed(url):
    feed_articles = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            raw_title = root.find('.//channel/title').text or "Unknown Source"
            clean_source = strip_to_clean_domain(raw_title, url)
            
            items = root.findall('.//item')[:3]
            for item in items:
                title = item.find('title').text
                link = item.find('link').text
                
                pub_date_raw = item.find('pubDate')
                if pub_date_raw is not None and pub_date_raw.text:
                    try:
                        dt = email.utils.parsedate_to_datetime(pub_date_raw.text)
                        dt_eastern = dt.astimezone(target_timezone)
                    except Exception:
                        dt_eastern = now_eastern
                else:
                    dt_eastern = now_eastern

                tags = []
                category_elements = item.findall('category')
                for cat in category_elements:
                    if cat.text:
                        cleaned_tag = cat.text.strip().lower()
                        if cleaned_tag and "/" not in cleaned_tag and len(cleaned_tag) < 25:
                            if cleaned_tag not in tags: tags.append(cleaned_tag)
                tags = tags[:5]

                feed_articles.append({
                    "title": title, 
                    "link": link, 
                    "source": clean_source,
                    "tags": tags,
                    "datetime": dt_eastern
                })
    except Exception as e:
        print(f"Error parsing {url}: {e}")
    return feed_articles

# Read feeds
with open("feeds.txt", "r", encoding="utf-8") as f:
    feeds = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

# OPTIMIZATION: Fetch all 30 feeds concurrently in parallel threads
articles_by_source = {}
unique_sources = set()

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(fetch_single_feed, feeds)
    for res in results:
        if res:
            source_name = res[0]["source"]
            unique_sources.add(source_name)
            # Sort each source individual stack by date
            res.sort(key=lambda x: x["datetime"], reverse=True)
            articles_by_source[source_name] = res

# VARIETY GENERATOR: Round-Robin interleaving logic
mixed_articles = []
while any(articles_by_source.values()):
    # Get all remaining active sources and sort them by the date of their freshest item
    active_sources = [s for s in articles_by_source if articles_by_source[s]]
    active_sources.sort(key=lambda s: articles_by_source[s][0]["datetime"], reverse=True)
    
    for source in active_sources:
        if articles_by_source[source]:
            mixed_articles.append(articles_by_source[source].pop(0))

# Generate HTML
current_time_str = now_eastern.strftime("%Y-%m-%d %I:%M %p ET")
sorted_sources = sorted(list(unique_sources))

toggle_switches_html = ""
for source in sorted_sources:
    toggle_switches_html += f'<span class="filter-btn active" onclick="toggleSource(\'{source}\', this)">[x] {source}</span> '

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terminal // Chronological_Feed</title>
    <style>
        body {{ 
            font-family: 'Courier New', Courier, monospace; 
            max-width: 900px; 
            margin: 40px auto; 
            padding: 0 20px; 
            background-color: #0d0d0d; 
            color: #00ff41; 
            line-height: 1.6; 
        }}
        ::selection {{ background: #00ff41; color: #000; }}
        h1 {{ 
            font-size: 1.6rem; 
            border-bottom: 1px dashed #00ff41; 
            padding-bottom: 10px; 
            margin-bottom: 5px;
            letter-spacing: 2px;
            text-transform: uppercase;
            text-shadow: 0 0 5px rgba(0, 255, 65, 0.5);
        }}
        .quote-box {{
            font-style: italic;
            color: #00ff41;
            opacity: 0.85;
            margin-top: 15px;
            margin-bottom: 5px;
            font-size: 0.95rem;
            word-wrap: break-word;
        }}
        .meta {{ color: #008f11; margin-bottom: 15px; font-size: 0.85rem; border-top: 1px dashed #008f11; padding-top: 5px; }}
        .filter-bar {{ font-size: 0.8rem; color: #008f11; margin-bottom: 30px; word-wrap: break-word; line-height: 2.0; }}
        .filter-btn {{ margin-right: 12px; cursor: pointer; user-select: none; white-space: nowrap; }}
        .filter-btn.active {{ color: #00ff41; text-shadow: 0 0 2px rgba(0, 255, 65, 0.4); }}
        .filter-btn.inactive {{ color: #00330b; }}
        ul {{ list-style-type: none; padding: 0; margin-top: 20px; }}
        li {{ margin-bottom: 18px; display: flex; flex-direction: column; align-items: flex-start; }}
        .link-row {{ display: flex; align-items: flex-start; width: 100%; border-bottom: 1px dotted rgba(255, 255, 255, 0.15); padding-bottom: 4px; }}
        .link-row::before {{ content: "> "; margin-right: 8px; color: #008f11; flex-shrink: 0; }}
        a {{ color: #00ff41; text-decoration: none; text-transform: uppercase; }}
        a:hover {{ background-color: #00ff41; color: #000; }}
        a:visited {{ color: #005f0c; }}
        .source {{ color: #008f11; font-size: 0.8rem; margin-left: 10px; white-space: nowrap; text-transform: lowercase; }}
        .tag-row {{ margin-left: 20px; font-size: 0.75rem; color: #008f11; opacity: 0.8; margin-top: 4px; word-wrap: break-word; }}
    </style>
</head>
<body>
    <h1>root@news:~# cat unified_timeline</h1>
    <div class="quote-box">{selected_quote}</div>
    <div class="meta">SYS_STATUS: ONLINE | TIMESTAMP: {current_time_str}</div>
    <div class="filter-bar"><span>FILTER_FLAGS: </span>{toggle_switches_html}</div>
    <ul>
"""

for art in mixed_articles:
    time_badge = compute_time_ago(art["datetime"], now_eastern)
    html_content += f'        <li data-source="{art["source"]}">\n            <div class="link-row"><a href="{art["link"]}" target="_blank">{art["title"]}</a><span class="source">[{art["source"]}]</span></div>\n'
    tag_build = f"posted: {time_badge}"
    if art["tags"]: tag_build += f" | tags: {' '.join([f'#{t}' for t in art['tags']])}"
    html_content += f'            <div class="tag-row">{tag_build}</div>\n        </li>\n'

html_content += """    </ul>
    <script>
        function toggleSource(sourceName, element) {
            const isCurrentlyActive = element.value || element.classList.contains('active');
            const articles = document.querySelectorAll('li[data-source="' + sourceName + '"]');
            if (isCurrentlyActive) {
                element.classList.remove('active');
                element.classList.add('inactive');
                element.innerText = '[ ] ' + sourceName;
                articles.forEach(el => el.style.display = 'none');
                element.value = false;
            } else {
                element.classList.add('active');
                element.classList.remove('inactive');
                element.innerText = '[x] ' + sourceName;
                articles.forEach(el => el.style.display = 'flex');
                element.value = true;
            }
        }
    </script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Optimized concurrent script successfully generated interleaved layout.")
