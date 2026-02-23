"""Unified Claude API client supporting both direct API and Claude Code modes."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass

from contentsifter.config import MODEL_DEFAULT

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    model: str


class AnthropicAPIClient:
    """Direct Anthropic API client using the anthropic Python SDK."""

    def __init__(self, api_key: str, model: str = MODEL_DEFAULT):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def complete(
        self, system: str, user: str, max_tokens: int = 8192
    ) -> LLMResponse:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return LLMResponse(
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=self.model,
        )


class ClaudeCodeClient:
    """Client that uses the claude CLI for LLM calls.

    Uses the `claude` CLI with --print flag. When running inside Claude Code,
    unsets the CLAUDECODE env var to allow nesting.
    """

    def __init__(self, model: str = MODEL_DEFAULT):
        self.model = model

    def complete(
        self, system: str, user: str, max_tokens: int = 8192
    ) -> LLMResponse:
        combined_prompt = f"{system}\n\n---\n\n{user}"
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        result = subprocess.run(
            ["claude", "--print", "--model", self.model, "-p", combined_prompt],
            capture_output=True,
            text=True,
            timeout=600,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI failed: {result.stderr}")
        return LLMResponse(
            content=result.stdout.strip(),
            input_tokens=0,
            output_tokens=0,
            model=self.model,
        )


# Global callback client — set by Claude Code when running interactively
_callback_client = None


class CallbackClient:
    """Client that delegates to a user-provided callback function.

    This is used when running inside Claude Code — the callback is set
    by the orchestrating code and calls the LLM directly.
    """

    def __init__(self, callback, model: str = MODEL_DEFAULT):
        self.callback = callback
        self.model = model

    def complete(
        self, system: str, user: str, max_tokens: int = 8192
    ) -> LLMResponse:
        content = self.callback(system, user)
        return LLMResponse(
            content=content,
            input_tokens=0,
            output_tokens=0,
            model=self.model,
        )


def set_callback_client(callback):
    """Set a callback function for Claude Code interactive mode.

    The callback should accept (system: str, user: str) -> str
    """
    global _callback_client
    _callback_client = CallbackClient(callback)


def create_client(
    mode: str = "auto", model: str = MODEL_DEFAULT
) -> AnthropicAPIClient | ClaudeCodeClient | CallbackClient:
    """Factory function for creating an LLM client.

    mode="auto": use API key if set, else callback client if set, else Claude Code CLI.
    mode="api": require ANTHROPIC_API_KEY.
    mode="claude-code": use Claude Code subprocess.
    """
    if mode == "auto":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            return AnthropicAPIClient(api_key, model)
        if _callback_client:
            return _callback_client
        return ClaudeCodeClient(model)
    elif mode == "api":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return AnthropicAPIClient(api_key, model)
    elif mode == "claude-code":
        if _callback_client:
            return _callback_client
        return ClaudeCodeClient(model)
    else:
        raise ValueError(f"Unknown LLM mode: {mode}")


def complete_with_retry(
    client,
    system: str,
    user: str,
    max_tokens: int = 8192,
    retries: int = 3,
    backoff: float = 2.0,
) -> LLMResponse:
    """Call the LLM with exponential backoff retries."""
    for attempt in range(retries):
        try:
            return client.complete(system, user, max_tokens)
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = backoff ** attempt
            logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
