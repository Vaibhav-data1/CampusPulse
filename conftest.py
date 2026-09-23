"""Pytest integration configuration for the repository-root test run."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "app" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# The backend historically exposes its package as ``app`` while analytics lives
# under the repository-level ``app/ml`` package. Extend the backend package path
# so both existing import layouts work during a root-level test run.
import app

analytics_package = ROOT / "app"
if str(analytics_package) not in app.__path__:
    app.__path__.append(str(analytics_package))
