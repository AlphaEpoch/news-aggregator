import datetime
import xml.etree.ElementTree as ET
import urllib.request

# Read your custom feeds
with open("feeds.txt", "r") as f:
    feeds = [line.strip() for line in f if line.strip()]

articles = []

# Fetch and parse feeds
for url in feeds:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # Find channel title
            channel_title = root.find('.//channel/title').text or "Unknown Source"
            
            # Grab top 5 items from each feed
            items = root.findall('.//item')[:5]
            for item in items:
                title = item.find('title').text
                link = item.find('link').text
                articles.append({"title": title, "link": link, "source": channel_title})
    except Exception as e:
        print(f"Error parsing {url}: {e}")

# Generate Minimalist Dark Matrix HTML
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terminal // News_Feed</title>
    <style>
        /* Matrix Terminal Aesthetic */
        body {{ 
            font-family: 'Courier New', Courier, monospace; 
            max-width: 900px; 
            margin: 40px auto; 
            padding: 0 20px; 
            background-color: #0d0d0d; 
            color: #00ff41; 
            line-height: 1.6; 
        }}
        
        /* Custom text selection colors */
        ::selection {{
            background: #00ff41;
            color: #000;
        }}

        h1 {{ 
            font-size: 1.6rem; 
            border-bottom: 1px dashed #00ff41; 
            padding-bottom: 10px; 
            letter-spacing: 2px;
            text-transform: uppercase;
            text-shadow: 0 0 5px rgba(0, 255, 65, 0.5);
        }}

        .meta {{ 
            color: #008f11; 
            margin-bottom: 30px; 
            font-size: 0.85rem; 
        }}

        ul {{ 
            list-style-type: none; 
            padding: 0; 
        }}

        li {{ 
            margin-bottom: 14px; 
            display: flex;
            align-items: flex-start;
        }}

        /* Terminal prompt pointer before each link */
        li::before {{
            content: "> ";
            margin-right: 8px;
            color: #008f11;
            flex-shrink: 0;
        }}

        a {{ 
            color: #00ff41; 
            text-decoration: none; 
        }}

        a:hover {{ 
            background-color: #00ff41;
            color: #000;
        }}

        .source {{ 
            color: #008f11; 
            font-size: 0.8rem; 
            margin-left: 10px; 
            white-space: nowrap;
        }}
    </style>
</head>
<body>
    <h1>root@news:~# cat latest_feeds</h1>
    <div class="meta">SYS_STATUS: ONLINE | TIMESTAMP: {current_time} | NODES: {len(feeds)}</div>
    <ul>
"""

for art in articles:
    html_content += f'        <li><a href="{art["link"]}" target="_blank">{art["title"]}</a><span class="source">[{art["source"]}]</span></li>\n'

html_content += """    </ul>
</body>
</html>"""

# Save the final static page
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Matrix terminal site built successfully!")
