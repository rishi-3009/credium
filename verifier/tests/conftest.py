import sys
from pathlib import Path

# Lets the tests import credium_sig from verifier/ without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
