import sys
from pathlib import Path

# Tests live in the skill; the tool is in the sibling scripts/ dir. Put that on the
# path so `import <module>` loads the tool directly — no symlink needed.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
