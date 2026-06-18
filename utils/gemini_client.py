"""
Gemini API client wrapper (menggunakan SDK baru `google-genai`).

Cara pakai:
    1. Install dependency:
        pip install google-genai

    2. Set API key sebagai environment variable:
        export GEMINI_API_KEY="your-api-key-here"   (Linux/Mac)
        setx GEMINI_API_KEY "your-api-key-here"      (Windows, lalu restart terminal)

    3. Import dan panggil:
        from utils.gemini_client import generate_text
        result = generate_text("Tulis ulang kalimat ini agar lebih sopan: ...")

Semua fungsi di sini FAIL-SAFE: jika API key tidak ada / request gagal,
fungsi mengembalikan None (bukan exception) supaya app tidak crash
saat fitur AI dipakai.
"""

import os
import time
import random

try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


_MODEL_NAME = "gemini-2.5-flash"
_client = None
_cached_api_key = None
_last_error = None

# Retry/backoff defaults (can be overridden via environment variables)
_DEFAULT_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0
_BACKOFF_JITTER = 0.5


def _get_client():

    global _client, _cached_api_key

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    if _client is not None and api_key == _cached_api_key:
        return _client

    if not _GENAI_AVAILABLE:
        return None

    _cached_api_key = api_key
    _client = genai.Client(api_key=api_key)

    return _client


# New API detection (if you set NEW_API_URL in .env, we'll prefer it)
_NEW_API_URL = os.environ.get("NEW_API_URL")
_NEW_API_KEY = os.environ.get("NEW_API_KEY")

try:
    from utils import new_api_client
except Exception:
    new_api_client = None


def is_available():
    """Cek apakah Gemini siap dipakai (library + API key tersedia)."""
    # Available if new API is configured, or the Gemini SDK + key is available
    if _NEW_API_URL:
        return True

    return _get_client() is not None


def _build_generation_config(max_output_tokens, temperature=None):
    config = {
        "max_output_tokens": max_output_tokens,
    }

    if temperature is not None:
        config["temperature"] = temperature

    thinking_config = getattr(genai_types, "ThinkingConfig", None)

    if thinking_config is not None:
        config["thinking_config"] = thinking_config(thinking_budget=0)

    return genai_types.GenerateContentConfig(**config)


def get_last_error() -> str | None:
    return _last_error


def generate_text(prompt, max_output_tokens=512, temperature=None):
    """
    Kirim prompt ke Gemini dan kembalikan teks hasil.
    Mengembalikan None jika Gemini tidak tersedia / terjadi error.
    """

    # If a NEW_API_URL is configured, delegate to the generic HTTP client.
    if _NEW_API_URL and new_api_client is not None:
        return new_api_client.generate_text(_NEW_API_URL, _NEW_API_KEY, prompt,
                                            max_output_tokens, temperature)

    client = _get_client()

    if client is None:
        return None

    # Allow overriding retry behavior via environment for flexibility in tests
    try:
        max_attempts = int(os.environ.get("GEMINI_MAX_RETRIES", _DEFAULT_MAX_RETRIES))
    except Exception:
        max_attempts = _DEFAULT_MAX_RETRIES

    try:
        backoff_base = float(os.environ.get("GEMINI_BACKOFF_BASE", _BACKOFF_BASE))
    except Exception:
        backoff_base = _BACKOFF_BASE

    try:
        backoff_jitter = float(os.environ.get("GEMINI_BACKOFF_JITTER", _BACKOFF_JITTER))
    except Exception:
        backoff_jitter = _BACKOFF_JITTER

    global _last_error

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=_MODEL_NAME,
                contents=prompt,
                config=_build_generation_config(max_output_tokens, temperature)
            )

            if not response.text:
                _last_error = "Gemini merespons tanpa teks hasil."
                return None

            _last_error = None
            return response.text.strip()

        except Exception as e:
            error_text = str(e)
            _last_error = error_text

            if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text:
                print(
                    "[Gemini Error] Quota exceeded or rate limit reached. "
                    "Periksa plan, billing, dan batas penggunaan API Anda."
                )
                print(f"[Gemini Details] {error_text}")
                return None

            last = (attempt == max_attempts - 1)
            if last:
                print(f"[Gemini Error] {e}")
                return None

            # Exponential backoff with jitter
            backoff = backoff_base * (2 ** attempt) + random.uniform(0, backoff_jitter)
            time.sleep(backoff)
            continue


# ==========================================================
# Prompt presets untuk fitur notepad
# ==========================================================

def rewrite_text(text):

    prompt = (
        "Tulis ulang teks berikut agar lebih jelas dan rapi, "
        "tetap dalam bahasa yang sama, jangan tambahkan komentar "
        "atau penjelasan apapun, hanya kembalikan hasil tulis ulangnya:\n\n"
        f"{text}"
    )

    return generate_text(prompt)


def summarize_text(text):

    prompt = (
        "Ringkas teks berikut menjadi maksimal 3 kalimat, "
        "gunakan bahasa yang sama dengan teks aslinya, "
        "jangan tambahkan komentar apapun:\n\n"
        f"{text}"
    )

    return generate_text(prompt)


def translate_text(text, target_language="English"):

    prompt = (
        f"Translate the following text to {target_language}. "
        "Only return the translated text, no explanation:\n\n"
        f"{text}"
    )

    return generate_text(prompt)


def continue_text(text):

    prompt = (
        "Lanjutkan tulisan berikut dengan 1-2 kalimat tambahan yang "
        "natural dan sesuai konteks. Hanya kembalikan kalimat "
        "lanjutannya saja (tanpa mengulang teks asli):\n\n"
        f"{text}"
    )

    return generate_text(prompt)


# ==========================================================
# Prompt presets untuk twist AI
# ==========================================================

def generate_roast(question, user_answer, correct_answer):
    """Untuk twist Self Aware Calculator - roast dinamis."""

    prompt = (
        "Kamu adalah kalkulator yang sombong dan suka meledek penggunanya "
        "dengan nada lucu/sarkastik (bukan kasar/menghina secara serius). "
        f"Soal: {question}. "
        f"Jawaban user: {user_answer}, jawaban benar: {correct_answer}. "
        "Buat satu kalimat roast singkat (maks 15 kata) dalam Bahasa "
        "Indonesia, jangan tambahkan tanda kutip atau penjelasan."
    )

    return generate_text(prompt, max_output_tokens=60)


def generate_riddle():
    """Untuk twist baru 'Riddle Master' - generate teka-teki + jawaban."""

    prompt = (
        "Buat satu teka-teki singkat dalam Bahasa Indonesia beserta "
        "jawabannya. Format output HARUS persis seperti ini, tanpa "
        "teks lain:\n"
        "RIDDLE: <teka-teki>\n"
        "ANSWER: <jawaban singkat 1-3 kata>"
    )

    raw = generate_text(prompt, max_output_tokens=120)

    if not raw:
        return None

    riddle = None
    answer = None

    for line in raw.splitlines():

        if line.upper().startswith("RIDDLE:"):
            riddle = line.split(":", 1)[1].strip()

        elif line.upper().startswith("ANSWER:"):
            answer = line.split(":", 1)[1].strip()

    if riddle and answer:
        return riddle, answer

    return None


def generate_possession_message():
    """Untuk twist baru 'AI Possession' - kalimat aneh yang disisipkan AI."""

    prompt = (
        "Buat SATU kalimat singkat (maks 12 kata) dalam Bahasa Indonesia "
        "yang terdengar seperti pesan misterius/creepy dari AI yang "
        "'menguasai' notepad pengguna. Jangan tambahkan tanda kutip."
    )

    return generate_text(prompt, max_output_tokens=40)
