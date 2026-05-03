with open(r'C:\stock-dashboard\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all lines with 'news-title'
for i, line in enumerate(lines):
    if 'news-title' in line:
        print(f"Line {i+1}: {line.rstrip()[:120]}")
