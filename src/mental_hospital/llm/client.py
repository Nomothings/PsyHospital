"""LLM chat client with automatic context management.

Each ``LLMClient`` maintains its own conversation history, allowing a
single agent instance to carry context across multiple calls (e.g. all
five interview phases).
"""

from __future__ import annotations

import base64
import logging
import time
from typing import List, Optional, Union

import httpx
from openai import OpenAI

from mental_hospital.config.constants import MAX_HISTORY_MESSAGES
from mental_hospital.config.settings import AgentConfig

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.ERROR)


class LLMClient:
    """OpenAI-compatible chat client with automatic history management.

    Parameters
    ----------
    config : AgentConfig
        API credentials and model parameters.
    system_message : str
        System prompt prepended to the conversation history.
    """

    def __init__(self, config: AgentConfig, system_message: str = "") -> None:
        self.config = config
        self._client = OpenAI(
            base_url=config.api_base,
            api_key=config.api_key,
            http_client=httpx.Client(verify=False, timeout=config.timeout),
        )
        self._history: list[dict[str, str]] = []
        if system_message:
            self._history.append({"role": "system", "content": system_message})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, message: str) -> str:
        """Send a user message; return the assistant reply.

        Conversation history is automatically maintained.
        """
        self._history.append({"role": "user", "content": message})
        self._trim_history()
        response = self._call_api(self._history)
        self._history.append({"role": "assistant", "content": response})
        return response

    def chat_with_history(self, messages: list[dict[str, str]]) -> str:
        """Call the API with an explicit message list (does not mutate history)."""
        return self._call_api(messages)

    def chat_with_images(
        self, message: str, image_paths: Union[str, list[str]]
    ) -> str:
        """Multimodal chat — attach base64-encoded images."""
        if isinstance(image_paths, str):
            image_paths = [image_paths]
        content: list = [{"type": "text", "text": message}]
        for path in image_paths:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{self._encode_image(path)}"},
            })
        self._history.append({"role": "user", "content": content})
        self._trim_history()
        response = self._call_api(self._history)
        self._history.append({"role": "assistant", "content": response})
        return response

    # ------------------------------------------------------------------
    # History management
    # ------------------------------------------------------------------

    def get_history(self) -> list[dict[str, str]]:
        return list(self._history)

    def clear_history(self) -> None:
        """Drop all messages except the system prompt."""
        self._history = [m for m in self._history if m["role"] == "system"]

    def reset(self) -> None:
        self._history = []

    def set_system_message(self, message: str) -> None:
        self._history = [m for m in self._history if m["role"] != "system"]
        self._history.insert(0, {"role": "system", "content": message})

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _trim_history(self) -> None:
        if len(self._history) <= MAX_HISTORY_MESSAGES:
            return
        system = [m for m in self._history if m["role"] == "system"]
        recent = self._history[-(MAX_HISTORY_MESSAGES - len(system)):]
        self._history = system + recent

    def _call_api(self, messages: list[dict[str, str]]) -> str:
        return _retry_with_backoff(lambda: self._do_call(messages))

    def _do_call(self, messages: list[dict[str, str]]) -> str:
        msgs = messages
        if self.config.uses_baichuan:
            msgs = _merge_system_into_user(messages)

        kwargs: dict = {
            "model": self.config.model,
            "messages": msgs,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout,
        }
        if self.config.uses_qwen:
            kwargs["extra_body"] = {"enable_thinking": False}

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    @staticmethod
    def _encode_image(image_path: str) -> str:
        with open(image_path, "rb") as fh:
            return base64.b64encode(fh.read()).decode("utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _retry_with_backoff(fn, max_retries: int = 3, base_delay: float = 1.0) -> str:
    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            logger.warning("API call failed (attempt %d/%d): %s", attempt + 1, max_retries, exc)
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
    raise last_error  # type: ignore[misc]


def _merge_system_into_user(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Move system-message content into the first user message (Baichuan compat)."""
    system_texts = [m["content"] for m in messages if m["role"] == "system"]
    others = [m for m in messages if m["role"] != "system"]
    if not system_texts:
        return others
    combined = "\n\n".join(system_texts)
    if others and others[0]["role"] == "user":
        others[0] = {"role": "user", "content": combined + "\n\n" + others[0]["content"]}
    else:
        others.insert(0, {"role": "user", "content": combined})
    return others
