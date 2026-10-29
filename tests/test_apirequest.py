from datetime import datetime
from pathlib import Path
import importlib.util
import unittest
import requests

# Resolve repo root and load backend module by file path.
ROOT = Path(__file__).resolve().parents[1]
APIREQUEST_PATH = ROOT / "backend" / "app" / "test" / "apirequest.py"

spec = importlib.util.spec_from_file_location("apirequest", APIREQUEST_PATH)
apirequest = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(apirequest)


class _FakeCollection:
    
    def __init__(self):
        self.inserted = []
        self.indexed_field = None

    def insert_one(self, document):
        self.inserted.append(document)

    def create_index(self, field):
        self.indexed_field = field


class TestApiRequest(unittest.TestCase):
    def setUp(self):
        self.old_getenv = apirequest.os.getenv
        self.old_get = apirequest.requests.get
        self.old_client = apirequest.pymongo.MongoClient
        self.old_get_weather = apirequest.get_weather
        self.old_transform = apirequest.transform_data
        self.old_save = apirequest.save_data
        apirequest.collection = None

    def tearDown(self):
        apirequest.os.getenv = self.old_getenv
        apirequest.requests.get = self.old_get
        apirequest.pymongo.MongoClient = self.old_client
        apirequest.get_weather = self.old_get_weather
        apirequest.transform_data = self.old_transform
        apirequest.save_data = self.old_save
        apirequest.collection = None

    def test_transform_data_maps_fields(self):
        # Representative API payload shape from OpenWeather.
        api_data = {
            "main": {
                "temp": 21.3,
                "humidity": 56,
                "temp_min": 20.1,
                "temp_max": 23.4,
            },
            "name": "Akron",
            "weather": [{"description": "clear sky"}],
        }

        record = apirequest.transform_data(api_data)

        self.assertEqual(record["zone"], "zone1")
        self.assertEqual(record["source"], "openweather")
        self.assertEqual(record["temp_c"], 21.3)
        self.assertEqual(record["humidity_pct"], 56)
        self.assertEqual(record["city"], "Akron")
        self.assertEqual(record["weather_desc"], "clear sky")
        self.assertIsInstance(record["ts"], datetime)

    def test_transform_data_sets_area(self):
        api_data = {
            "main": {
                "temp": 21.3,
                "humidity": 56,
                "temp_min": 20.1,
                "temp_max": 23.4,
            },
            "name": "Akron",
            "weather": [{"description": "clear sky"}],
        }

        record = apirequest.transform_data(api_data)
        self.assertEqual(record["area"], "upper_plants")

    def test_transform_data_sets_sensor_type(self):
        api_data = {
            "main": {
                "temp": 21.3,
                "humidity": 56,
                "temp_min": 20.1,
                "temp_max": 23.4,
            },
            "name": "Akron",
            "weather": [{"description": "clear sky"}],
        }

        record = apirequest.transform_data(api_data)
        self.assertEqual(record["sensor_type"], "weather")

    def test_transform_data_sets_temp_min_and_max(self):
        api_data = {
            "main": {
                "temp": 21.3,
                "humidity": 56,
                "temp_min": 20.1,
                "temp_max": 23.4,
            },
            "name": "Akron",
            "weather": [{"description": "clear sky"}],
        }

        record = apirequest.transform_data(api_data)
        self.assertEqual(record["temp_min"], 20.1)
        self.assertEqual(record["temp_max"], 23.4)

    def test_save_data_inserts_when_collection_exists(self):
        # Inject fake collection so test does not depend on a real database.
        fake_collection = _FakeCollection()
        apirequest.collection = fake_collection

        payload = {"zone": "zone1", "temp_c": 22.0}
        apirequest.save_data(payload)

        self.assertEqual(len(fake_collection.inserted), 1)
        self.assertEqual(fake_collection.inserted[0], payload)

    def test_save_data_does_nothing_when_collection_is_none(self):
        payload = {"zone": "zone1", "temp_c": 22.0}
        apirequest.collection = None

        apirequest.save_data(payload)

        self.assertIsNone(apirequest.collection)

    def test_save_data_does_nothing_when_payload_is_none(self):
        fake_collection = _FakeCollection()
        apirequest.collection = fake_collection

        apirequest.save_data(None)

        self.assertEqual(len(fake_collection.inserted), 0)

    def test_get_weather_returns_none_when_api_key_missing(self):
        apirequest.os.getenv = lambda key: None

        result = apirequest.get_weather()

        self.assertIsNone(result)

    def test_get_weather_returns_data_on_success(self):
        apirequest.os.getenv = lambda key: "fake_key"

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "main": {
                        "temp": 18.5,
                        "humidity": 70,
                        "temp_min": 17.0,
                        "temp_max": 20.0,
                    },
                    "name": "Akron",
                    "weather": [{"description": "cloudy"}],
                }

        apirequest.requests.get = lambda *args, **kwargs: FakeResponse()

        result = apirequest.get_weather()

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Akron")
        self.assertEqual(result["main"]["temp"], 18.5)

    def test_get_weather_returns_none_on_request_exception(self):
        apirequest.os.getenv = lambda key: "fake_key"

        def bad_get(*args, **kwargs):
            raise requests.RequestException("API failed")

        apirequest.requests.get = bad_get

        result = apirequest.get_weather()

        self.assertIsNone(result)

    def test_collect_data_to_db_calls_transform_and_save(self):
        saved = []

        apirequest.get_weather = lambda: {"main": {}, "weather": [{}], "name": "Akron"}
        apirequest.transform_data = lambda data: {"done": True}
        apirequest.save_data = lambda data: saved.append(data)

        apirequest.collect_data_to_db()

        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0], {"done": True})

    def test_collect_data_to_db_does_nothing_when_get_weather_returns_none(self):
        saved = []

        apirequest.get_weather = lambda: None
        apirequest.save_data = lambda data: saved.append(data)

        apirequest.collect_data_to_db()

        self.assertEqual(len(saved), 0)

    def test_init_db_collection_sets_collection_on_success(self):
        class FakeClient:
            def __init__(self, *args, **kwargs):
                self.admin = self
                self.fake_collection = _FakeCollection()

            def command(self, cmd):
                return {"ok": 1}

            def __getitem__(self, name):
                return {"weather_data": self.fake_collection}

        apirequest.pymongo.MongoClient = FakeClient

        apirequest.init_db_collection()

        self.assertIsNotNone(apirequest.collection)
        self.assertEqual(apirequest.collection.indexed_field, "ts")

    def test_init_db_collection_sets_none_on_failure(self):
        def bad_client(*args, **kwargs):
            raise Exception("DB failed")

        apirequest.pymongo.MongoClient = bad_client

        apirequest.init_db_collection()

        self.assertIsNone(apirequest.collection)

        def test_transform_data_sets_source(self):
            api_data = {
                "main": {
                    "temp": 21.3,
                    "humidity": 56,
                    "temp_min": 20.1,
                    "temp_max": 23.4,
                },
                "name": "Akron",
                "weather": [{"description": "clear sky"}],
            }
            record = apirequest.transform_data(api_data)
            self.assertEqual(record["source"], "openweather")

    def test_transform_data_sets_zone(self):
        api_data = {
            "main": {
                "temp": 21.3,
                "humidity": 56,
                "temp_min": 20.1,
                "temp_max": 23.4,
            },
            "name": "Akron",
            "weather": [{"description": "clear sky"}],
        }

        record = apirequest.transform_data(api_data)
        self.assertEqual(record["zone"], "zone1")

    def test_transform_data_sets_city(self):
        api_data = {
            "main": {
                "temp": 21.3,
                "humidity": 56,
                "temp_min": 20.1,
                "temp_max": 23.4,
            },
            "name": "Akron",
            "weather": [{"description": "clear sky"}],
        }

        record = apirequest.transform_data(api_data)
        self.assertEqual(record["city"], "Akron")

    def test_get_weather_contains_weather_list_on_success(self):
        apirequest.os.getenv = lambda key: "fake_key"

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "main": {
                        "temp": 18.5,
                        "humidity": 70,
                        "temp_min": 17.0,
                        "temp_max": 20.0,
                    },
                    "name": "Akron",
                    "weather": [{"description": "cloudy"}],
                }

        apirequest.requests.get = lambda *args, **kwargs: FakeResponse()

        result = apirequest.get_weather()

        self.assertEqual(result["weather"][0]["description"], "cloudy")

    def test_save_data_keeps_multiple_inserts(self):
        fake_collection = _FakeCollection()
        apirequest.collection = fake_collection

        apirequest.save_data({"temp_c": 20.0})
        apirequest.save_data({"temp_c": 21.0})

        self.assertEqual(len(fake_collection.inserted), 2)
    
        def test_transform_data_sets_area_again(self):
            api_data = {
                "main": {
                    "temp": 25.0,
                    "humidity": 50,
                    "temp_min": 22.0,
                    "temp_max": 27.0,
                },
                "name": "Kent",
                "weather": [{"description": "sunny"}],
            }

            record = apirequest.transform_data(api_data)
            self.assertEqual(record["area"], "upper_plants")

    def test_transform_data_sets_sensor_type_again(self):
        api_data = {
            "main": {
                "temp": 25.0,
                "humidity": 50,
                "temp_min": 22.0,
                "temp_max": 27.0,
            },
            "name": "Kent",
            "weather": [{"description": "sunny"}],
        }

        record = apirequest.transform_data(api_data)
        self.assertEqual(record["sensor_type"], "weather")

    def test_transform_data_sets_temp_min(self):
        api_data = {
            "main": {
                "temp": 25.0,
                "humidity": 50,
                "temp_min": 22.0,
                "temp_max": 27.0,
            },
            "name": "Kent",
            "weather": [{"description": "sunny"}],
        }

        record = apirequest.transform_data(api_data)
        self.assertEqual(record["temp_min"], 22.0)

    def test_transform_data_sets_temp_max(self):
        api_data = {
            "main": {
                "temp": 25.0,
                "humidity": 50,
                "temp_min": 22.0,
                "temp_max": 27.0,
            },
            "name": "Kent",
            "weather": [{"description": "sunny"}],
        }

        record = apirequest.transform_data(api_data)
        self.assertEqual(record["temp_max"], 27.0)

    def test_transform_data_uses_new_city_value(self):
        api_data = {
            "main": {
                "temp": 19.0,
                "humidity": 61,
                "temp_min": 17.0,
                "temp_max": 21.0,
            },
            "name": "Cleveland",
            "weather": [{"description": "rain"}],
        }

        record = apirequest.transform_data(api_data)
        self.assertEqual(record["city"], "Cleveland")

    def test_get_weather_success_has_humidity(self):
        apirequest.os.getenv = lambda key: "fake_key"

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "main": {
                        "temp": 18.5,
                        "humidity": 70,
                        "temp_min": 17.0,
                        "temp_max": 20.0,
                    },
                    "name": "Akron",
                    "weather": [{"description": "cloudy"}],
                }

        apirequest.requests.get = lambda *args, **kwargs: FakeResponse()

        result = apirequest.get_weather()
        self.assertEqual(result["main"]["humidity"], 70)

    def test_get_weather_success_has_temp_max(self):
        apirequest.os.getenv = lambda key: "fake_key"

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "main": {
                        "temp": 18.5,
                        "humidity": 70,
                        "temp_min": 17.0,
                        "temp_max": 20.0,
                    },
                    "name": "Akron",
                    "weather": [{"description": "cloudy"}],
                }

        apirequest.requests.get = lambda *args, **kwargs: FakeResponse()

        result = apirequest.get_weather()
        self.assertEqual(result["main"]["temp_max"], 20.0)

    def test_save_data_keeps_first_insert_value(self):
        fake_collection = _FakeCollection()
        apirequest.collection = fake_collection

        apirequest.save_data({"temp_c": 20.0})
        apirequest.save_data({"temp_c": 21.0})

        self.assertEqual(fake_collection.inserted[0]["temp_c"], 20.0)

    def test_save_data_keeps_second_insert_value(self):
        fake_collection = _FakeCollection()
        apirequest.collection = fake_collection

        apirequest.save_data({"temp_c": 20.0})
        apirequest.save_data({"temp_c": 21.0})

        self.assertEqual(fake_collection.inserted[1]["temp_c"], 21.0)

    def test_collect_data_to_db_saves_once(self):
        saved = []

        apirequest.get_weather = lambda: {"main": {}, "weather": [{}], "name": "Akron"}
        apirequest.transform_data = lambda data: {"done": True}
        apirequest.save_data = lambda data: saved.append(data)

        apirequest.collect_data_to_db()

        self.assertEqual(len(saved), 1)


if __name__ == "__main__":
    unittest.main()