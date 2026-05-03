with open(r'C:\stock-dashboard\app.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix the clickable link - the quotes need to be escaped properly for f-strings
# Current broken: href="{article['url']}"
# Should be: href=\"{article['url']}\"

# Find the broken patterns and fix them
old1 = '''f"<div class='news-title'><a href="{article['url']}" target="_blank" style='color:#e2e8f0;text-decoration:none;' onmouseover="this.style.color='#60a5fa'" onmouseout="this.style.color='#e2e8f0'">{article['title']}</a></div>'''

new1 = """f"<div class='news-title'><a href=\\"{article['url']}\\" target=\\"_blank\\" style='color:#e2e8f0;text-decoration:none;' onmouseover=\\"this.style.color='#60a5fa'\\" onmouseout=\\"this.style.color='#e2e8f0'\\">{article['title']}</a></div>"""

# Replace both instances
count = c.count(old1)
print(f"Found {count} instances")

c = c.replace(old1, new1)

with open(r'C:\stock-dashboard\app.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Fixed!")
