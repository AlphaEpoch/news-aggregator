import datetime
import xml.etree.ElementTree as ET
import urllib.request
import random

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

articles_by_category = {}
current_category = "UNCATEGORIZED"

# Read feeds and parse on the fly to preserve category order
with open("feeds.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        # If the line is a comment/category marker
        if line.startswith("#"):
            current_category = line.replace("#", "").strip()
            if current_category and current_category not in articles_by_category:
                articles_by_category[current_category] = []
            continue

        # If it's a URL, parse it under the current category
        url = line
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                channel_title = root.find('.//channel/title').text or "Unknown Source"
                items = root.findall('.//item')[:5]
                
                if current_category not in articles_by_category:
                    articles_by_category[current_category] = []

                for item in items:
                    title = item.find('title').text
                    link = item.find('link').text
                    
                    # Tag/Category Extraction Logic
                    tags = []
                    category_elements = item.findall('category')
                    for cat in category_elements:
                        if cat.text:
                            cleaned_tag = cat.text.strip().lower()
                            # Skip long taxonomy paths or empty strings
                            if cleaned_tag and "/" not in cleaned_tag and len(cleaned_tag) < 25:
                                if cleaned_tag not in tags:
                                    tags.append(cleaned_tag)
                    
                    # Limit to the top 5 unique tags
                    tags = tags[:5]

                    articles_by_category[current_category].append({
                        "title": title, 
                        "link": link, 
                        "source": channel_title,
                        "tags": tags
                    })
        except Exception as e:
            print(f"Error parsing {url}: {e}")

# Generate HTML
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terminal // News_Feed</title>
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
        .category-header {{
            font-size: 1.1rem;
            color: #00ff41;
            margin-top: 40px;
            margin-bottom: 15px;
            font-weight: bold;
            text-shadow: 0 0 3px rgba(0, 255, 65, 0.3);
        }}
        .meta {{ color: #008f11; margin-bottom: 20px; font-size: 0.85rem; border-top: 1px dashed #008f11; padding-top: 5px; }}
        ul {{ list-style-type: none; padding: 0; margin-bottom: 30px; }}
        
        /* Adjusted layout to house tags cleanly underneath */
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
        }}
        .link-row::before {{ content: "> "; margin-right: 8px; color: #008f11; flex-shrink: 0; }}
        
        a {{ color: #00ff41; text-decoration: none; }}
        a:hover {{ background-color: #00ff41; color: #000; }}
        .source {{ color: #008f11; font-size: 0.8rem; margin-left: 10px; white-space: nowrap; }}
        
        /* Terminal Meta Tags Row Style */
        .tag-row {{
            margin-left: 20px;
            font-size: 0.75rem;
            color: #008f11;
            opacity: 0.8;
            margin-top: 2px;
            word-wrap: break-word;
        }}
        .tag {{
            margin-right: 8px;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <h1>root@news:~# cat latest_feeds</h1>
    <div class="quote-box">{selected_quote}</div>
    <div class="meta">SYS_STATUS: ONLINE | TIMESTAMP: {current_time}</div>
"""

for cat_name, articles in articles_by_category.items():
    if not articles: 
        continue
        
    html_content += f'    <div class="category-header">{cat_name}</div>\n    <ul>\n'
    
    for art in articles:
        # Build main line row
        html_content += f'        <li>\n            <div class="link-row"><a href="{art["link"]}" target="_blank">{art["title"]}</a><span class="source">[{art["source"]}]</span></div>\n'
        
        # Build tags sub-row if tags exist
        if art["tags"]:
            tag_strings = [f"#{t}" for t in art["tags"]]
            html_content += f'            <div class="tag-row">tags: {" ".join(tag_strings)}</div>\n'
            
        html_content += "        </li>\n"
        
    html_content += "    </ul>\n"

html_content += """</body>
</html>"""

# Save the final file
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Categorized site with sub-tags built successfully!")
