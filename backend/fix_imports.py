import os
import re

ROOT = "backend"

# (old, new) 패턴 목록
REPLACEMENTS = [
    (r'from\s+agents\.', 'from core.agents.'),
    (r'from\s+tools\.', 'from core.tools.'),
    (r'from\s+llm_providers\.', 'from core.llm_providers.'),
    (r'from\s+embeddings\.', 'from core.embeddings.'),
    (r'from\s+config\s+import', 'from core.config import'),
    (r'import\s+agents\.', 'import core.agents.'),
    (r'import\s+tools\.', 'import core.tools.'),
    (r'import\s+llm_providers\.', 'import core.llm_providers.'),
    (r'import\s+embeddings\.', 'import core.embeddings.'),
]

def fix_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    original = content
    for old, new in REPLACEMENTS:
        content = re.sub(old, new, content)
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated: {filepath}")

def walk_and_fix(root):
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".py"):
                fix_file(os.path.join(dirpath, filename))

if __name__ == "__main__":
    walk_and_fix(ROOT)
    print("✅ Import 경로 일괄 수정 완료!")