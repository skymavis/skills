import sys
from pathlib import Path

# Put the repo's scripts/ on the path so `import validate_skills` works.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
