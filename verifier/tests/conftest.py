import sys
from pathlib import Path

# Lets the tests import credium_sig from verifier/ without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Lets the tests import verifier.verify and sim.* from the project root (api/main.py does the same).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
