#!/usr/bin/env python3
"""Static submission gate checks – run without Docker."""
import pathlib, sys, re

ROOT = pathlib.Path(__file__).parent

checks = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    checks.append((name, status, detail))
    print(f"{status}: {name} {detail}")

# 1. Required files
required = ["README.md","docker-compose.yml","Dockerfile",".env.example","downstream/validate_data.py","backend","frontend"]
for r in required:
    check(f"file {r}", (ROOT/r).exists())

# 2. .env.example
env = ROOT/".env.example"
if env.exists():
    txt = env.read_text(encoding="utf-8", errors="replace")
    check(".env.example DATABASE_URL", "DATABASE_URL" in txt)
    check(".env.example LLM_PROVIDER", "LLM_PROVIDER" in txt)
    check(".env.example no real key", "sk-" not in txt and "ghp_" not in txt)
else:
    check(".env.example exists", False)

# 3. .gitignore
gi = ROOT/".gitignore"
if gi.exists():
    txt = gi.read_text(encoding="utf-8", errors="replace")
    check(".gitignore .env", re.search(r"^\.env$", txt, re.M))
    check(".gitignore node_modules", "node_modules" in txt)
else:
    check(".gitignore exists", False)

# 4. README basics
rm = ROOT/"README.md"
if rm.exists():
    txt = rm.read_text(encoding="utf-8", errors="replace")
    check("README Quick Start", "docker-compose up --build" in txt.lower())
    check("README API table", "/api" in txt)
else:
    check("README exists", False)

# 5. Backend structure
check("backend/app/main.py", (ROOT/"backend/app/main.py").exists())
check("backend/app/models/models.py", (ROOT/"backend/app/models/models.py").exists())
check("backend/app/api/router.py", (ROOT/"backend/app/api/router.py").exists())

# 6. Frontend structure
check("frontend/package.json", (ROOT/"frontend/package.json").exists())

# 7. Docker compose health
dc = ROOT/"docker-compose.yml"
if dc.exists():
    txt = dc.read_text(encoding="utf-8", errors="replace")
    check("docker-compose healthcheck", "healthcheck" in txt)
    check("docker-compose db service", "db:" in txt)
    check("docker-compose app service", "app:" in txt)
else:
    check("docker-compose.yml", False)

print("\nSummary")
for n,s,d in checks:
    print(f"{s}\t{n}")

fails = [c for c in checks if c[1]=="FAIL"]
sys.exit(1 if fails else 0)
