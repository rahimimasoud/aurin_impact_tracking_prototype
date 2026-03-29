"""
Google Gemini implementation of AIProvider.

Reads GEMINI_API_KEY from the environment (loaded via .env) and calls
the gemini-2.5-flash model to produce the impact summary.
"""
import os
from dotenv import load_dotenv

from components.ai_summary.base import AIProvider, ImpactContext, SUMMARY_PROMPT_TEMPLATE
load_dotenv()

_MODEL = "gemini-2.5-flash"


class GeminiProvider(AIProvider):
    """AIProvider backed by Google Gemini generative AI."""

    def is_available(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))

    def generate_summary(self, context: ImpactContext) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )

        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError(
                "google-generativeai is not installed. Run: uv add google-generativeai"
            )

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_MODEL)
        prompt = SUMMARY_PROMPT_TEMPLATE.format(context=context.to_text())
        response = model.generate_content(prompt)
        return response.text
