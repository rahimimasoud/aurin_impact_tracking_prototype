"""
Google Gemini implementation of AIProvider.

Reads GEMINI_API_KEY from the environment (loaded via .env) and calls
the gemini-2.5-flash model to produce the impact summary.
"""
from components.ai_summary.base import AIProvider, ImpactContext, SUMMARY_PROMPT_TEMPLATE

_MODEL = "gemini-2.5-flash"


class GeminiProvider(AIProvider):
    """AIProvider backed by Google Gemini generative AI."""

    def __init__(self, api_key: str = None):
        self._api_key = api_key

    def _resolve_key(self) -> str:
        return self._api_key or ""

    def is_available(self) -> bool:
        return bool(self._resolve_key())

    def generate_summary(self, context: ImpactContext) -> str:
        api_key = self._resolve_key()
        if not api_key:
            raise RuntimeError(
                "Gemini API key is not set. Enter it in the sidebar to enable AI summaries."
            )

        try:
            from google import genai
        except ImportError:
            raise RuntimeError(
                "google-genai is not installed. Run: uv add google-genai"
            )

        client = genai.Client(api_key=api_key)
        prompt = SUMMARY_PROMPT_TEMPLATE.format(context=context.to_text())
        response = client.models.generate_content(model=_MODEL, contents=prompt)
        return response.text
