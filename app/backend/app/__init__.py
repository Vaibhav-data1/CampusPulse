"""CampusPulse backend package.

The repository-level ``app/ml`` package is exposed as a sibling namespace so
the backend can reuse the shared analytics and anomaly modules when launched
from ``app/backend``.
"""

from pathlib import Path


__path__.append(str(Path(__file__).resolve().parents[2]))
