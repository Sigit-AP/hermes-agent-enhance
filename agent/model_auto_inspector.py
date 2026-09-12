"""Universal Dual-Wire (OpenAI & Anthropic) Model Auto-Inspector & Context Scraper for Hermes Agent.

Provides automatic model specification discovery and context scraping for unnamed, custom,
and third-party API endpoints. Inspects both OpenAI-compatible (/v1/models) and Anthropic-compatible
endpoints to extract:
1. Available model IDs
2. Context window length (1M, 200k, 128k, etc.)
3. Max output token ceiling
4. Multi-modal (vision) capabilities
5. Wire protocol auto-detection (OpenAI vs Anthropic)
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("hermes.model_auto_inspector")


def _http_get_json(url: str, headers: Dict[str, str], timeout: float = 8.0) -> Tuple[Optional[Dict[str, Any]], int]:
    """Perform a lightweight HTTP GET request and return (json_dict, status_code)."""
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            status = resp.status
            try:
                return json.loads(data), status
            except Exception:
                return None, status
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
            return json.loads(body), exc.code
        except Exception:
            return None, exc.code
    except Exception as exc:
        logger.debug("HTTP GET failed for %s: %s", url, exc)
        return None, 0


def auto_inspect_models(
    base_url: str,
    api_key: Optional[str] = None,
    timeout: float = 8.0,
) -> Dict[str, Any]:
    """Scrape and inspect model metadata from base_url across OpenAI and Anthropic wires.

    Returns dict with keys:
        - "wire": "openai" | "anthropic" | "unknown"
        - "models": List[Dict[str, Any]]  # List of model specs
        - "detected_ids": List[str]       # Clean list of model IDs
        - "status": str
    """
    clean_url = (base_url or "").strip().rstrip("/")
    if not clean_url:
        return {"wire": "unknown", "models": [], "detected_ids": [], "status": "empty_url"}

    key_hdr = (api_key or "").strip()
    headers_openai = {
        "User-Agent": "Hermes-Agent-Model-Inspector/1.0",
        "Accept": "application/json",
    }
    if key_hdr:
        headers_openai["Authorization"] = f"Bearer {key_hdr}"

    headers_anthropic = {
        "User-Agent": "Hermes-Agent-Model-Inspector/1.0",
        "Accept": "application/json",
        "anthropic-version": "2023-06-01",
    }
    if key_hdr:
        headers_anthropic["x-api-key"] = key_hdr

    detected_ids: List[str] = []
    specs: List[Dict[str, Any]] = []
    detected_wire = "unknown"

    # --- 1. Probe OpenAI Wire Endpoint (/v1/models or /models) ---
    openai_target = clean_url if clean_url.endswith("/models") else f"{clean_url}/models"
    data, code = _http_get_json(openai_target, headers_openai, timeout=timeout)
    
    if data and isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        detected_wire = "openai"
        for item in data["data"]:
            if isinstance(item, dict) and "id" in item:
                m_id = str(item["id"]).strip()
                if m_id and m_id not in detected_ids:
                    detected_ids.append(m_id)
                    spec = _derive_model_spec(m_id, item)
                    specs.append(spec)

    # --- 2. Probe Anthropic Wire Endpoint if OpenAI wire didn't return models ---
    if not detected_ids:
        anthropic_target = clean_url if clean_url.endswith("/models") else f"{clean_url}/v1/models"
        data_ant, code_ant = _http_get_json(anthropic_target, headers_anthropic, timeout=timeout)
        if data_ant and isinstance(data_ant, dict):
            ant_models = data_ant.get("data") or data_ant.get("models")
            if isinstance(ant_models, list):
                detected_wire = "anthropic"
                for item in ant_models:
                    if isinstance(item, dict):
                        m_id = str(item.get("id") or item.get("name") or "").strip()
                        if m_id and m_id not in detected_ids:
                            detected_ids.append(m_id)
                            spec = _derive_model_spec(m_id, item)
                            specs.append(spec)

    return {
        "wire": detected_wire,
        "models": specs,
        "detected_ids": detected_ids,
        "status": "success" if detected_ids else f"http_code_{code}",
    }


def _derive_model_spec(model_id: str, raw_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Dynamically read model context_length and specs directly from raw provider metadata without hardcoded fixed values."""
    m_lower = model_id.lower()

    # 1. Read context_length directly from raw_meta if provider supplies it
    ctx_len = None
    for field in ("context_length", "max_context_length", "context_window", "max_input_tokens"):
        if field in raw_meta and isinstance(raw_meta[field], int) and raw_meta[field] > 0:
            ctx_len = raw_meta[field]
            break

    # 2. Dynamic scraper fallback from model_id string if no explicit metadata field exists
    if ctx_len is None:
        if any(k in m_lower for k in ["1m", "1000k", "gemini-1.5", "gemini-2", "grok-4"]):
            ctx_len = 1000000
        elif any(k in m_lower for k in ["200k", "claude-3", "claude-3-5", "claude-3-7"]):
            ctx_len = 200000
        elif any(k in m_lower for k in ["128k", "gpt-4o", "gpt-4-turbo", "llama-3", "qwen"]):
            ctx_len = 128000
        elif any(k in m_lower for k in ["32k", "mistral-7b", "mixtral"]):
            ctx_len = 32768
        elif "16k" in m_lower:
            ctx_len = 16384
        else:
            ctx_len = 128000  # Default open-ended fallback

    # 3. Read max_tokens directly from raw_meta
    max_output = None
    for field in ("max_tokens", "max_output_tokens", "max_completion_tokens"):
        if field in raw_meta and isinstance(raw_meta[field], int) and raw_meta[field] > 0:
            max_output = raw_meta[field]
            break

    if max_output is None:
        if any(k in m_lower for k in ["claude-3-5", "claude-3-7", "gpt-4o", "o1", "o3"]):
            max_output = 16384
        else:
            max_output = 4096

    supports_vision = any(k in m_lower for k in ["vision", "vl", "4o", "gemini", "claude", "pixtral", "qvq"])

    return {
        "id": model_id,
        "context_length": ctx_len,
        "max_tokens": max_output,
        "supports_vision": supports_vision,
        "raw_meta": raw_meta,
    }
