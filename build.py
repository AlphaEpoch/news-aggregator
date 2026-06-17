import datetime
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET
import urllib.request
import random
import email.utils

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

all_articles = []
target_timezone = ZoneInfo("America/New_York")

# Read feeds
with open("feeds.txt", "r", encoding="utf-8") as f:
    # Read URLs and ignore comments (#) or empty lines
    feeds = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

# Fetch and parse feeds
for url in feeds:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            channel_title = root.find('.//channel/title').text or "Unknown Source"
            
            # STRICT LIMIT: Slice down to only pull the top 3 items per source
            items = root.findall('.//item')[:3]
            
            for item in items:
                title = item.find('title').text
                link = item.find('link').text
                
                # Timestamp parsing logic
                pub_date_raw = item.find('pubDate')
                if pub_date_raw is not None and pub_date_raw.text:
                    try:
                        # Convert RSS time string into a timezone-aware datetime object
                        dt = email.utils.parsedate_to_datetime(pub_date_raw.text)
                        # Normalize time to Eastern Time for consistent sorting
                        dt_eastern = dt.astimezone(target_timezone)
                    except Exception:
                        dt_eastern = datetime.datetime.now(target_timezone)
                else:
                    dt_eastern = datetime.datetime.now(target_timezone)

                # Tag Extraction Logic
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
                    "source": channel_title,
                    "tags": tags,
                    "datetime": dt_eastern
                })
    except Exception as e:
        print(f"Error parsing {url}: {e}")

# CHRONOLOGICAL SORT: Newest posts at the very top of the feed
all_articles.sort(key=lambda x: x["datetime"], reverse=True)

# Generate HTML
current_time = datetime.datetime.now(target_timezone).strftime("%Y-%m-%d %I:%M %p ET")

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
        .meta {{ color: #008f11; margin-bottom: 30px; font-size: 0.85rem; border-top: 1px dashed #008f11; padding-top: 5px; }}
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
        .source {{ color: #008f11; font-size: 0.8rem; margin-left: 10px; white-space: nowrap; }}
        
        /* Styled time string layout next to tags */
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
    <h1>root@news:</h1>
    <div class="quote-box">{selected_quote}</div>
    <div class="meta">SYS_STATUS: ONLINE | TIMESTAMP: {current_time}</div>
    
    <ul>
"""

# Render the single unified timeline list
for art in all_articles:
    time_str = art["datetime"].strftime("%m/%d %I:%M %p")
    html_content += f'        <li>\n            <div class="link-row"><a href="{art["link"]}" target="_blank">{art["title"]}</a><span class="source">[{art["source"]}]</span></div>\n'
    
    # Render time badge and optional tags directly underneath
    tag_build = f"posted: {time_str}"
    if art["tags"]:
        tag_build += f" | tags: {' '.join([f'#{t}' for t in art['tags']])}"
        
    html_content += f'            <div class="tag-row">{tag_build}</div>\n        </li>\n'

html_content += """    </ul>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Unified chronological timeline compiled successfully.")
