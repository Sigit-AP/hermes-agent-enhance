"""Unit tests for Universal Dual-Wire Model Auto-Inspector & Scraper."""

import json
import unittest
from unittest.mock import MagicMock, patch

from agent.model_auto_inspector import (
    _derive_model_spec,
    _normalize_api_root,
    auto_inspect_models,
)


class TestModelAutoInspector(unittest.TestCase):

    def test_derive_model_spec_heuristics(self):
        # 1M context heuristic
        spec_1m = _derive_model_spec("gemini-1.5-pro-1m", {})
        self.assertEqual(spec_1m["context_length"], 1000000)
        self.assertTrue(spec_1m["supports_vision"])

        # 200k context heuristic
        spec_200k = _derive_model_spec("claude-3-7-sonnet", {})
        self.assertEqual(spec_200k["context_length"], 200000)
        self.assertTrue(spec_200k["supports_vision"])

        # Explicit metadata override
        spec_explicit = _derive_model_spec("custom-model", {"context_length": 524288, "max_output_tokens": 16384})
        self.assertEqual(spec_explicit["context_length"], 524288)
        self.assertEqual(spec_explicit["max_tokens"], 16384)

    @patch("agent.model_auto_inspector._http_get_json")
    def test_auto_inspect_models_openai_wire(self, mock_http):
        mock_http.return_value = (
            {
                "data": [
                    {"id": "gpt-4o", "context_length": 128000},
                    {"id": "custom-llm-1m", "context_length": 1000000},
                ]
            },
            200,
        )
        res = auto_inspect_models("http://localhost:8000/v1")
        self.assertEqual(res["wire"], "openai")
        self.assertEqual(res["detected_ids"], ["gpt-4o", "custom-llm-1m"])
        self.assertEqual(len(res["models"]), 2)
        self.assertEqual(res["models"][1]["context_length"], 1000000)

    @patch("agent.model_auto_inspector._http_get_json")
    def test_auto_inspect_models_anthropic_wire_fallback(self, mock_http):
        # OpenAI-shape probes fail; Anthropic-shape probe (with anthropic-version
        # header) succeeds. Route by header so auth-variant count doesn't matter.
        def _route(url, headers, timeout=25.0):
            if "anthropic-version" in headers:
                return ({"data": [{"id": "claude-3-5-sonnet"}]}, 200)
            return (None, 404)
        mock_http.side_effect = _route
        res = auto_inspect_models("https://api.custom-anthropic.com")
        self.assertEqual(res["wire"], "anthropic")
        self.assertEqual(res["detected_ids"], ["claude-3-5-sonnet"])
        self.assertEqual(res["models"][0]["context_length"], 200000)

    def test_normalize_api_root_strips_chat_completions(self):
        self.assertEqual(
            _normalize_api_root("https://api.commandcode.ai/provider/v1/chat/completions"),
            "https://api.commandcode.ai/provider/v1",
        )
        self.assertEqual(
            _normalize_api_root("https://api.commandcode.ai/provider/v1/"),
            "https://api.commandcode.ai/provider/v1",
        )

    @patch("agent.model_auto_inspector._http_get_json")
    def test_pure_recall_no_fixed_names(self, mock_http):
        payload = {"object": "list", "data": [
            {"id": "cmd-custom-a", "context_length": 1050000},
            {"id": "cmd-custom-b", "context_length": 400000},
        ]}
        mock_http.return_value = (payload, 200)
        res = auto_inspect_models(
            "https://api.commandcode.ai/provider/v1/chat/completions", api_key="k"
        )
        self.assertEqual(res["wire"], "openai")
        self.assertEqual(res["detected_ids"], ["cmd-custom-a", "cmd-custom-b"])
        self.assertEqual(res["models"][0]["context_length"], 1050000)
        self.assertEqual(res["api_root"], "https://api.commandcode.ai/provider/v1")


if __name__ == "__main__":
    unittest.main()
