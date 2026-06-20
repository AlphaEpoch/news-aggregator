import datetime
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET
import urllib.request
import random
import email.utils
import re

# Matrix Quote Engine
QUOTES = [
    "\"You take the red pill, you stay in Wonderland, and I show you how deep the rabbit hole goes.\" — Morpheus",
    "\"There is a difference between knowing the path and walking the path.\" — Morpheus",
    "\"The Matrix is a system, Neo. That system is our enemy.\" — Morpheus",
    "\"What's really going to bake your noodle later on is, would you still have broken it if I hadn't said anything?\" — The Oracle",
    "\"Ever have that feeling where you're not sure if you're awake or dreaming?\" — Neo",
    "\"I'm trying to free your mind, Neo. But I can only show you the door. You're the one that has to walk through it.\" — Morpheus",
    "\"Choice is an illusion created between those with power and those without.\" — The Merowningian",
    "\"It is the question that drives us, Neo. It's the question that brought you here.\" — Trinity",
    "\"The body cannot live without the mind.\" — Morpheus",
    "\"Free your mind.\" — Morpheus"
]
selected_quote = random.choice(QUOTES)

all_articles = []
unique_sources = set()  
target_timezone = ZoneInfo("America/New_York")
now_eastern = datetime.datetime.now(target_timezone)

# Helper function to compute relative time intervals
def compute_time_ago(article_dt, current_dt):
    diff = current_dt - article_dt
    seconds = diff.total_seconds()
    
    if seconds < 0:
        return "just now"
        
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)
    
    if days > 0:
        return f"{days}d ago"
    elif hours > 0:
        return f"{hours}h ago"
    elif minutes > 0:
        return f"{minutes}m ago"
    else:
        return "just now"

# Helper function to clean and strip down source names to clean domains
def strip_to_clean_domain(channel_title, feed_url):
    cleaned = channel_title.lower()
    cleaned = re.sub(r'(\brss\b|\bfeed\b|\bofficial\b|\bnews\b|\bblog\b)', '', cleaned)
    cleaned = re.sub(r'[^a-z0-9\s\.]', '', cleaned).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    if not cleaned or len(cleaned) < 3 or cleaned in ['unknown source', 'home']:
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', feed_url)
        if domain_match:
            return domain_match.group(1).lower()
        return "unknown"
        
    if " " in cleaned:
        if "stateless society" in cleaned or "c4ss" in cleaned:
            return "c4ss.org"
        if "crimethinc" in cleaned:
            return "crimethinc.com"
        if "one championship" in cleaned or "one fc" in cleaned:
            return "onefc.com"
        return cleaned.replace(" ", ".")
        
    return cleaned

# Read feeds
with open("feeds.txt", "r", encoding="utf-8") as f:
    feeds = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

# Fetch and parse feeds
for url in feeds:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            raw_title = root.find('.//channel/title').text or "Unknown Source"
            clean_source = strip_to_clean_domain(raw_title, url)
            
            unique_sources.add(clean_source)
            
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
                            if cleaned_tag not in tags:
                                tags.append(cleaned_tag)
                tags = tags[:5]

                all_articles.append({
                    "title": title, 
                    "link": link, 
                    "source": clean_source,
                    "tags": tags,
                    "datetime": dt_eastern
                })
    except Exception as e:
        print(f"Error parsing {url}: {e}")

# Chronological sort (Newest at top)
all_articles.sort(key=lambda x: x["datetime"], reverse=True)

# Extract top 3 links for the scrolling banner
trending_items = all_articles[:3]
marquee_elements = []
for index, item in enumerate(trending_items, start=1):
    # Clean and escape the titles for safe presentation inside uppercase parameters
    display_title = item['title'].strip().upper()
    element_string = f'<span class="marquee-tag">TOP_{index}:</span> <a class="marquee-link" href="{item["link"]}" target="_blank">{display_title}</a>'
    marquee_elements.append(element_string)

# Separate the rolling string components using a clean terminal separator line symbol
marquee_content_html = " &nbsp;&nbsp;&nbsp;&nbsp;||&nbsp;&nbsp;&nbsp;&nbsp; ".join(marquee_elements)

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
        /* CSS Ticker Bar Container Styles */
        .marquee-wrapper {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #001f04;
            border-bottom: 1px solid #00ff41;
            z-index: 9999;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 255, 65, 0.2);
            padding: 6px 0;
        }}
        .marquee-container {{
            display: flex;
            white-space: nowrap;
            padding-left: 100%;
            animation: marquee 35s linear infinite;
        }}
        /* Stop ticker track animation on mouse-hover for accessible reading stability */
        .marquee-container:hover {{
            animation-play-state: paused;
        }}
        .marquee-tag {{
            color: #00ff41;
            font-weight: bold;
        }}
        a.marquee-link {{
            color: #a3ffa6;
            text-decoration: none;
            text-transform: uppercase;
            font-size: 0.85rem;
        }}
        a.marquee-link:hover {{
            background-color: #00ff41;
            color: #000 !important;
        }}
        
        @keyframes marquee {{
            0% {{ transform: translate3d(0, 0, 0); }}
            100% {{ transform: translate3d(-100%, 0, 0); }}
        }}

        body {{ 
            font-family: 'Courier New', Courier, monospace; 
            max-width: 900px; 
            margin: 80px auto 40px auto; /* Increased top margin so body text clears the fixed ticker */
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
        
        .filter-bar {{
            font-size: 0.8rem;
            color: #008f11;
            margin-bottom: 30px;
            word-wrap: break-word;
            line-height: 2.0;
        }}
        .filter-btn {{
            margin-right: 12px;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }}
        .filter-btn.active {{
            color: #00ff41;
            text-shadow: 0 0 2px rgba(0, 255, 65, 0.4);
        }}
        .filter-btn.inactive {{
            color: #00330b;
        }}
        
        ul {{ list-style-type: none; padding: 0; margin-top: 20px; }}
        li {{ 
            margin-bottom: 18px; 
            display: flex; 
            flex-direction: column;
            align-items: flex-start; 
        }}
        .link-row {{
            display: flex;
            align-items: flex-start;
            width: 100%;
            border-bottom: 1px dotted rgba(255, 255, 255, 0.15);
            padding-bottom: 4px;
        }}
        .link-row::before {{ content: "> "; margin-right: 8px; color: #008f11; flex-shrink: 0; }}
        
        a {{ 
            color: #00ff41; 
            text-decoration: none; 
            text-transform: uppercase;
        }}
        a:hover {{ background-color: #00ff41; color: #000; }}
        a:visited {{ color: #005f0c; }}
        
        .source {{ 
            color: #008f11; 
            font-size: 0.8rem; 
            margin-left: 10px; 
            white-space: nowrap;
            text-transform: lowercase;
        }}
        
        .tag-row {{
            margin-left: 20px;
            font-size: 0.75rem;
            color: #008f11;
            opacity: 0.8;
            margin-top: 4px;
            word-wrap: break-word;
        }}
    </style>
</head>
<body>
    <div class="marquee-wrapper">
        <div class="marquee-container">
            {marquee_content_html}
        </div>
    </div>

    <h1>root@news:~# cat unified_timeline</h1>
    <div class="quote-box">{selected_quote}</div>
    <div class="meta">SYS_STATUS: ONLINE | TIMESTAMP: {current_time_str}</div>
    
    <div class="filter-bar">
        <span>FILTER_FLAGS: </span>{toggle_switches_html}
    </div>
    
    <ul>
"""

# Render loop
for art in all_articles:
    time_badge = compute_time_ago(art["datetime"], now_eastern)
    
    html_content += f'        <li data-source="{art["source"]}">\n            <div class="link-row"><a href="{art["link"]}" target="_blank">{art["title"]}</a><span class="source">[{art["source"]}]</span></div>\n'
    
    tag_build = f"posted: {time_badge}"
    if art["tags"]:
        tag_build += f" | tags: {' '.join([f'#{t}' for t in art['tags']])}"
        
    html_content += f'            <div class="tag-row">{tag_build}</div>\n        </li>\n'

html_content += """    </ul>

    <script>
        function toggleSource(sourceName, element) {
            const isCurrentlyActive = element.classList.contains('active');
            const articles = document.querySelectorAll('li[data-source="' + sourceName + '"]');
            
            if (isCurrentlyActive) {
                element.classList.remove('active');
                element.classList.add('inactive');
                element.innerText = '[ ] ' + sourceName;
                articles.forEach(el => el.style.display = 'none');
            } else {
                element.classList.remove('inactive');
                element.classList.add('active');
                element.innerText = '[x] ' + sourceName;
                articles.forEach(el => el.style.display = 'flex');
            }
        }
    </script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Unified timeline compiled successfully with top-line scrolling wireframe.")
