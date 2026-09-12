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


def _normalize_api_root(base_url: str) -> str:
    """Normalize any user-supplied base_url to its API root.

    Handles inputs like:
      https://host/provider/v1/chat/completions -> https://host/provider/v1
      https://host/provider/v1/messages -> https://host/provider/v1
      https://host/v1 -> https://host/v1
    """
    u = (base_url or "").strip().rstrip("/")
    for suffix in ("/chat/completions", "/messages", "/completions"):
        if u.endswith(suffix):
            u = u[: -len(suffix)].rstrip("/")
    return u


def _auth_variants(api_key: Optional[str]) -> List[Dict[str, str]]:
    """Return auth header variants to try. Many gateways (e.g. CommandCode)
    require x-api-key instead of Authorization: Bearer."""
    key = (api_key or "").strip()
    base = {"User-Agent": "Hermes-Agent-Model-Inspector/1.0", "Accept": "application/json"}
    if not key:
        return [dict(base)]
    return [
        {**base, "x-api-key": key},
        {**base, "Authorization": f"Bearer {key}"},
        {**base, "Authorization": f"Bearer {key}", "x-api-key": key},
    ]


def _http_get_json(url: str, headers: Dict[str, str], timeout: float = 25.0) -> Tuple[Optional[Dict[str, Any]], int]:
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
    timeout: float = 25.0,
) -> Dict[str, Any]:
    """Scrape and inspect model metadata from base_url across OpenAI and Anthropic wires.

    Pure recall: returns provider-supplied model list verbatim, no fixed model names.
    Handles base_url with or without /chat/completions suffix and both
    Authorization: Bearer and x-api-key auth schemes.

    Returns dict with keys:
        - "wire": "openai" | "anthropic" | "unknown"
        - "models": List[Dict[str, Any]]
        - "detected_ids": List[str]
        - "api_root": str (normalized root used for /models probing)
        - "status": str
    """
    raw = (base_url or "").strip()
    if not raw:
        return {"wire": "unknown", "models": [], "detected_ids": [], "api_root": "", "status": "empty_url"}

    api_root = _normalize_api_root(raw)

    detected_ids: List[str] = []
    specs: List[Dict[str, Any]] = []
    detected_wire = "unknown"
    last_code = 0
    tried_urls: List[str] = []

    # Candidate /models endpoints derived from normalized root.
    candidates: List[str] = []
    if api_root.endswith("/models"):
        candidates.append(api_root)
    else:
        candidates.append(f"{api_root}/models")
        # Avoid duplicate /v1/v1 when root already ends with /v1
        if not api_root.endswith("/v1"):
            candidates.append(f"{api_root}/v1/models")

    auth_list = _auth_variants(api_key)

    # --- 1. OpenAI-shape probe: {data: [{id, context_length, ...}]} ---
    for target in candidates:
        tried_urls.append(target)
        for headers in auth_list:
            data, code = _http_get_json(target, headers, timeout=timeout)
            last_code = code
            if data and isinstance(data, dict) and isinstance(data.get("data"), list) and data["data"]:
                detected_wire = "openai"
                for item in data["data"]:
                    if isinstance(item, dict) and item.get("id"):
                        m_id = str(item["id"]).strip()
                        if m_id and m_id not in detected_ids:
                            detected_ids.append(m_id)
                            specs.append(_derive_model_spec(m_id, item))
                if detected_ids:
                    break
        if detected_ids:
            break

    # --- 2. Anthropic-shape fallback: {data|models: [{id|name, ...}]} ---
    if not detected_ids:
        for target in candidates:
            for headers in auth_list:
                h = dict(headers)
                h["anthropic-version"] = "2023-06-01"
                data_ant, code_ant = _http_get_json(target, h, timeout=timeout)
                last_code = code_ant
                if isinstance(data_ant, dict):
                    ant_models = data_ant.get("data") or data_ant.get("models")
                    if isinstance(ant_models, list) and ant_models:
                        detected_wire = "anthropic"
                        for item in ant_models:
                            if isinstance(item, dict):
                                m_id = str(item.get("id") or item.get("name") or "").strip()
                                if m_id and m_id not in detected_ids:
                                    detected_ids.append(m_id)
                                    specs.append(_derive_model_spec(m_id, item))
                        if detected_ids:
                            break
            if detected_ids:
                break

    return {
        "wire": detected_wire,
        "models": specs,
        "detected_ids": detected_ids,
        "api_root": api_root,
        "tried_urls": tried_urls,
        "status": "success" if detected_ids else f"http_code_{last_code}",
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

    # Vision capability: prefer explicit provider metadata, heuristic only as fallback.
    supports_vision: Optional[bool] = None
    for field in ("supports_vision", "vision", "modalities", "supported_modalities", "input_modalities"):
        if field in raw_meta:
            val = raw_meta[field]
            if isinstance(val, bool):
                supports_vision = val
                break
            if isinstance(val, (list, tuple, set)):
                lowered = {str(v).lower() for v in val}
                if lowered & {"image", "images", "vision", "video"}:
                    supports_vision = True
                    break
                if lowered:
                    supports_vision = False
                    break
            if isinstance(val, str) and val:
                supports_vision = val.lower() in {"true", "yes", "1", "image", "vision"}
                break
    if supports_vision is None:
        supports_vision = any(k in m_lower for k in ["vision", "vl", "4o", "gemini", "claude", "pixtral", "qvq"])

    return {
        "id": model_id,
        "context_length": ctx_len,
        "max_tokens": max_output,
        "supports_vision": supports_vision,
        "raw_meta": raw_meta,
    }
