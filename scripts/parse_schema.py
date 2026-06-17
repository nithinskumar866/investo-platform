import sys, json, re

data = sys.stdin.read()
match = re.search(r'\{.*\}', data, re.DOTALL)
if match:
    schema = json.loads(match.group())
    paths = sorted(schema.get("paths", {}).keys())
    for p in paths:
        print(p)
    print(f"\nTotal paths: {len(paths)}")
else:
    print("No valid JSON found")
