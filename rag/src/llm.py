import os
from typing import List, Dict, Any

import requests
from dotenv import load_dotenv


# Load .env automatically when this module is imported
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()


class DeepSeekClient:
    """
    Minimal client for DeepSeek OpenAI-compatible chat completions.

    DeepSeek exposes OpenAI-style endpoints. You send:
      POST {base_url}/v1/chat/completions
    With Authorization: Bearer <key>
    """

    def __init__(
        self,
        api_key: str = DEEPSEEK_API_KEY,
        base_url: str = DEEPSEEK_BASE_URL,
        model: str = DEEPSEEK_MODEL,
        timeout_s: int = 120,
    ):
        if not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is missing. Put it in .env or set it in your environment."
            )

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 300) -> str:
        """
        Call DeepSeek chat completions and return assistant text.

        messages format:
          [{"role":"system","content":"..."}, {"role":"user","content":"..."}]
        """
        url = f"{self.base_url}/v1/chat/completions"

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout_s)
        r.raise_for_status()

        data = r.json()
        # OpenAI-style: choices[0].message.content
        return data["choices"][0]["message"]["content"].strip()