from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from src.utils.crypto import encrypt_trace_data

logger = structlog.get_logger(__name__)


def _decode_salt(salt_b64: str | None) -> bytes | None:
    if not salt_b64:
        return None
    try:
        import base64

        return base64.b64decode(salt_b64)
    except Exception:
        return None


class TraceLogger:
    """Logs LLM calls, graph executions, and metadata to disk.

    When encryption_passphrase is set, all data is encrypted at rest using
    AES-256-GCM with a PBKDF2-derived key. The server cannot read traces
    without the user's session passphrase.
    """

    def __init__(
        self,
        job_id: str,
        encryption_passphrase: str | None = None,
        encryption_salt: str | None = None,
    ):
        self.job_id = job_id
        self.encryption_passphrase = encryption_passphrase
        self.encryption_salt = encryption_salt
        self.base_path = f"storage/traces/{job_id}"
        os.makedirs(self.base_path, exist_ok=True)
        self.traces: List[Dict[str, Any]] = []

    def _maybe_encrypt_and_write(self, filename: str, data: Dict[str, Any]) -> None:
        """Write data to disk, optionally encrypting it first."""
        if self.encryption_passphrase and self.encryption_salt:
            # Encrypt the JSON-serialized data
            plaintext = json.dumps(data, indent=2)
            encrypted_b64, salt_b64 = encrypt_trace_data(
                plaintext, self.encryption_passphrase, salt=_decode_salt(self.encryption_salt)
            )
            encrypted_payload = {
                "encrypted": encrypted_b64,
                "salt": salt_b64,
                "encryption": "AES-256-GCM+PBKDF2",
                "encrypted_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(filename, "w") as f:
                json.dump(encrypted_payload, f, indent=2)
        else:
            # Plaintext path (e.g. Ollama local — no API key needed)
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)

    def log_llm_call(
        self,
        step: str,
        prompt: str,
        response: str,
        model: str,
        duration: float,
    ):
        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "model": model,
            "prompt": prompt,
            "response": response,
            "duration": duration,
        }
        self.traces.append(trace_entry)

        timestamp = int(time.time() * 1000)
        filename = f"{self.base_path}/{timestamp}_{step}.json"
        self._maybe_encrypt_and_write(filename, trace_entry)

        logger.info("trace.llm_call", job_id=self.job_id, step=step, duration=duration)

    def save_graph_execution(self, graph_state: Dict[str, Any]) -> None:
        # Strip sensitive fields before saving (belt-and-suspenders)
        safe_state = _strip_sensitive_fields(graph_state)
        filename = f"{self.base_path}/graph_execution.json"
        self._maybe_encrypt_and_write(filename, safe_state)
        logger.info("trace.graph_saved", job_id=self.job_id)

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        safe_meta = {k: v for k, v in metadata.items() if k not in _SENSITIVE_KEYS}
        filename = f"{self.base_path}/metadata.json"
        self._maybe_encrypt_and_write(filename, safe_meta)
        logger.info("trace.metadata_saved", job_id=self.job_id)


_SENSITIVE_KEYS = frozenset({
    "openrouter_api_key",
    "api_key",
    "encrypted_api_key",
    "encryption_iv",
    "encryption_salt",
    "encryption_passphrase",
})


def _strip_sensitive_fields(state: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive key material from the graph state before saving."""
    result: Dict[str, Any] = {}
    for k, v in state.items():
        if k in _SENSITIVE_KEYS:
            result[k] = "*** REDACTED ***"
        elif isinstance(v, dict):
            result[k] = _strip_sensitive_fields(v)
        else:
            result[k] = v
    return result
