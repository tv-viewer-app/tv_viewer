#!/usr/bin/env python3
"""Helper script to organize TV Viewer project for GitHub."""
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# Create docs directory
os.makedirs(DOCS_DIR, exist_ok=True)
print(f"Created: {DOCS_DIR}")

# Files to move to docs folder
docs_files = [
    "CODE_REVIEW.md",
    "UX_AUDIT.md", 
    "SECURITY_AUDIT.md",
    "TEST_PLAN.md",
    "SUPPORT_GUIDE.md",
    "ARCHITECTURE.md",
    "PERFORMANCE.md",
    "API.md",
]

for filename in docs_files:
    src = os.path.join(BASE_DIR, filename)
    dst = os.path.join(DOCS_DIR, filename)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Moved: {filename} -> docs/")
    else:
        print(f"Skipped (not found): {filename}")

# Create PRD.md
prd_path = os.path.join(DOCS_DIR, "PRD.md")
if os.path.exists(os.path.join(BASE_DIR, "_create_prd.py")):
    # Execute the PRD creation script logic
    exec(open(os.path.join(BASE_DIR, "_create_prd.py")).read())
    print("PRD.md created")

# Clean up helper scripts
cleanup_files = ["_create_prd.py", "organize_project.py"]
for f in cleanup_files:
    path = os.path.join(BASE_DIR, f)
    if os.path.exists(path):
        os.remove(path)
        print(f"Cleaned up: {f}")

# Create .gitignore if not exists
gitignore_path = os.path.join(BASE_DIR, ".gitignore")
if not os.path.exists(gitignore_path):
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Build artifacts
*.spec
*.exe
*.dmg
*.app

# Project specific
channels.json
thumbnails/
*.log

# OS
.DS_Store
Thumbs.db
"""
    with open(gitignore_path, 'w') as f:
        f.write(gitignore_content)
    print("Created: .gitignore")

print("\nProject organized! Ready for git init and push to GitHub.")
print("\nNext steps:")
print("1. Run: git init")
print("2. Run: git add .")
print("3. Run: git commit -m 'Initial commit: TV Viewer IPTV application'")
print("4. Create repo on GitHub: gh repo create arielsaghiv/tv-viewer --private")
print("5. Run: git remote add origin https://github.com/arielsaghiv/tv-viewer.git")
print("6. Run: git push -u origin main")
