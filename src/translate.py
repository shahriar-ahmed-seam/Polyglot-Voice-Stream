"""Text translation using a Groq-hosted LLM."""
from groq import Groq

from .config import settings

_LANG_NAMES = {
    "en": "English", "es": "Spanish", "ja": "Japanese", "fr": "French",
    "de": "German", "hi": "Hindi", "zh": "Chinese", "pt": "Portuguese",
}


class Translator:
    def __init__(self) -> None:
        self.client = Groq(api_key=settings.groq_api_key)
        self.src = _LANG_NAMES.get(settings.source_lang, settings.source_lang)
        self.tgt = _LANG_NAMES.get(settings.target_lang, settings.target_lang)

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""
        resp = self.client.chat.completions.create(
            model=settings.llm_model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a real-time interpreter. Translate the user's "
                        f"{self.src} text into {self.tgt}. Output only the translation, "
                        f"with no notes or quotes, and preserve the original tone."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        return resp.choices[0].message.content.strip()
