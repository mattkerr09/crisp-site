"""Explicit engine fixture for offline sale tests. Production readers never import it.

The parallel Crisp job owns the engine update. This fixture exercises its agreed
constant names without changing, or falling back from, the real engine file.
"""
from contextlib import contextmanager
from unittest.mock import Mock, patch

import llms_txt

ENGINE_SOURCE = '''PRICE_USD = 19
FOUNDING_OFF_USD = 9.01
NOVEMBER_PRICE_USD = 14.50
LAUNCH_ENDS = "2026-12-03T07:59:59Z"
SALE_PERCENT_OFF = round((NOVEMBER_PRICE_USD - (PRICE_USD - FOUNDING_OFF_USD)) / NOVEMBER_PRICE_USD * 100)
FREE_EXPORT_CAP_SECONDS = 15
'''


@contextmanager
def sale_engine():
    with patch.object(llms_txt, 'ENGINE', Mock(read_text=Mock(return_value=ENGINE_SOURCE))):
        yield
