import os
import sys
from unittest.mock import MagicMock

# Add src to path so tests can import modules directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# The tests never open a browser. Stubbing nodriver lets them run where it is
# not installed.
if "nodriver" not in sys.modules:
    try:
        import nodriver  # noqa: F401
    except ImportError:
        sys.modules["nodriver"] = MagicMock()
