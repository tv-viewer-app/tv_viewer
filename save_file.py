import sys
content = sys.stdin.read()
with open(sys.argv[1], 'w') as f:
    f.write(content)
print(f"✓ Saved {sys.argv[1]} ({len(content)} bytes)")
