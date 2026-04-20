"""
OpenRouter implementation of AIProvider using the OpenAI SDK against OpenRouter's
OpenAI-compatible endpoint.
"""
import re
from openai import OpenAI
from components.ai_summary.base import AIProvider, ImpactContext, SUMMARY_PROMPT_TEMPLATE

_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_MODEL = "openrouter/auto"


class OpenRouterProvider(AIProvider):
    """AIProvider backed by OpenRouter."""

    def __init__(self, api_key: str = None, model: str = _DEFAULT_MODEL):
        self._api_key = api_key
        self._model = model

    def _resolve_key(self) -> str:
        return self._api_key or ""

    def is_available(self) -> bool:
        return bool(self._resolve_key())

    def generate_summary(self, context: ImpactContext) -> str:
        api_key = self._resolve_key()
        if not api_key:
            raise RuntimeError(
                "OpenRouter API key is not set. Enter it in the sidebar to enable AI summaries."
            )

        client = OpenAI(api_key=api_key, base_url=_BASE_URL)
        prompt = SUMMARY_PROMPT_TEMPLATE.format(context=context.to_text())
        response = client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            timeout=60,
        )
        content = response.choices[0].message.content
        content = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', content)
        content = re.sub(r'`([^`\n]+)`', r'\1', content)
        content = content.replace('$', r'\$')
        return content
