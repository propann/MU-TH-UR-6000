"""Tests unitaires du registre et des adaptateurs sûrs du rack Mother."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import veille  # noqa: E402


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _limit):
        return json.dumps(self.payload).encode()


class FakeRequest:
    def __init__(self, path, body=None):
        self.path = path
        self.headers = {"Host": "localhost", "Origin": "http://localhost"}
        self.client_address = ("127.0.0.1", 50000)
        self.payload = body or {}
        self.max_body = None

    def authorized(self):
        return True

    def is_internal_rack_caller(self):
        return veille.Handler.is_internal_rack_caller(self)

    def same_origin(self):
        return True

    def body(self, max_bytes=2_000_000):
        self.max_body = max_bytes
        return self.payload

    def send(self, status, body, *_args, **_kwargs):
        return status, body


class RackTests(unittest.TestCase):
    def setUp(self):
        self.original_cache = veille.cache
        veille.cache = {}

    def tearDown(self):
        veille.cache = self.original_cache

    def test_catalogue_matches_manifest_and_only_exposes_three_adapters(self):
        catalog = veille.rack_capabilities(veille.load_rack())["capabilities"]
        callable_ids = {item["id"] for item in catalog if item["state"] == "callable"}
        self.assertEqual(callable_ids, {
            "ai.models.list", "watch.articles.search", "trading.status.read",
        })
        self.assertTrue(all(item["permission"] == "read_only" for item in catalog if item["state"] == "callable"))

    def test_article_search_uses_only_cached_http_articles(self):
        veille.cache = {"fixture": {"items": [
            {"id": "safe", "title": "Mother rack update", "summary": "local test",
             "link": "https://example.invalid/article", "source": "Fixture", "cat": "IA", "date": 10},
            {"id": "unsafe", "title": "Mother rack update", "link": "javascript:alert(1)", "date": 20},
        ]}}
        status, result = veille.call_rack_capability("watch.articles.search", {"query": "Mother rack"})
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["data"]["cached_only"])
        self.assertEqual([item["id"] for item in result["data"]["items"]], ["safe"])

    def test_ollama_adapter_returns_minimal_catalogue(self):
        payload = {"models": [{"name": "qwen3:8b", "digest": "hidden",
                               "details": {"family": "qwen3", "parameter_size": "8B",
                                           "quantization_level": "Q4_K_M"}}]}
        with patch.object(veille.urllib.request, "urlopen", return_value=FakeResponse(payload)):
            status, result = veille.call_rack_capability("ai.models.list", {})
        self.assertEqual(status, 200)
        self.assertEqual(result["data"]["models"][0]["name"], "qwen3:8b")
        self.assertNotIn("digest", json.dumps(result))

    def test_trading_adapter_reports_health_only(self):
        with patch.object(veille, "probe", return_value={"online": True, "detail": None}):
            status, result = veille.call_rack_capability("trading.status.read", {})
        self.assertEqual(status, 200)
        self.assertEqual(result["data"], {"online": True, "declared_mode": "dry-run", "detail": "API Quant Core"})

    def test_declared_write_capability_is_not_executable(self):
        status, result = veille.call_rack_capability("workspace.files.write", {"path": "/tmp/should-not-exist"})
        self.assertEqual(status, 409)
        self.assertEqual(result["error"]["code"], "not_connected")
        self.assertFalse(Path("/tmp/should-not-exist").exists())

    def test_invalid_inputs_have_normalized_errors(self):
        status, result = veille.call_rack_capability("watch.articles.search", {"query": "x", "url": "https://example.invalid"})
        self.assertEqual(status, 400)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["data"], None)
        self.assertIn("duration_ms", result)

    def test_capability_http_routes_and_small_post_limit(self):
        request = FakeRequest("/api/rack/capabilities")
        status, result = veille.Handler.do_GET(request)
        self.assertEqual(status, 200)
        self.assertTrue(result["capabilities"])

        request = FakeRequest("/api/rack/call", {
            "capability": "watch.articles.search", "input": {"query": "no matches"},
        })
        status, result = veille.Handler.do_POST(request)
        self.assertEqual(status, 200)
        self.assertEqual(request.max_body, 16_384)
        self.assertEqual(result["status"], "ok")

    def test_capability_http_route_rejects_non_object_json(self):
        request = FakeRequest("/api/rack/call", ["not", "an", "object"])
        status, result = veille.Handler.do_POST(request)
        self.assertEqual(status, 400)
        self.assertIn("objet JSON", result["error"])

    def test_internal_bridge_is_loopback_only_and_rejects_proxy_headers(self):
        request = FakeRequest("/api/rack/internal/call")
        self.assertFalse(veille.Handler.is_internal_rack_caller(request))
        request.headers.pop("Origin")
        request.headers.pop("X-Forwarded-For", None)
        request.headers.pop("Forwarded", None)
        self.assertTrue(veille.Handler.is_internal_rack_caller(request))
        request.headers["X-Forwarded-For"] = "192.168.2.7"
        self.assertFalse(veille.Handler.is_internal_rack_caller(request))

    def test_internal_bridge_executes_read_only_call_only_from_loopback(self):
        local = FakeRequest("/api/rack/internal/call", {
            "capability": "watch.articles.search", "input": {"query": "cached search"},
        })
        local.headers.pop("Origin")
        status, result = veille.Handler.do_POST(local)
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "ok")

        remote = FakeRequest("/api/rack/internal/call", {
            "capability": "watch.articles.search", "input": {"query": "cached search"},
        })
        remote.headers.pop("Origin")
        remote.client_address = ("192.168.2.7", 50000)
        status, result = veille.Handler.do_POST(remote)
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
