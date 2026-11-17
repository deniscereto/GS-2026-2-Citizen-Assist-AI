import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from assistente import Assistente  # noqa: E402


@pytest.fixture(scope="session")
def assistente():
    return Assistente()
