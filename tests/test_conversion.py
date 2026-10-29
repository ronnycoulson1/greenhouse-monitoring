from pathlib import Path
import importlib.util
import unittest

# Resolve repo root and import the conversion utility directly from file path.
ROOT = Path(__file__).resolve().parents[1]
CONVERSION_PATH = ROOT / "frontend" / "streamlit_app" / "utils" / "conversion.py"

spec = importlib.util.spec_from_file_location("conversion", CONVERSION_PATH)
conversion = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(conversion)
fahrenheitToCelsius = conversion.fahrenheitToCelsius


class TestConversion(unittest.TestCase):
    def test_fahrenheit_to_celsius_known_values(self):
        # Verify a few canonical conversion points.
        self.assertEqual(fahrenheitToCelsius(32), 0.0)
        self.assertEqual(fahrenheitToCelsius(68), 20.0)
        self.assertEqual(fahrenheitToCelsius(-40), -40.0)


if __name__ == "__main__":
    unittest.main()
