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

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


_MODEL_NAME = "gemini-2.5-flash"
_client = None


def _get_client():

    global _client

    if _client is not None:
        return _client

    if not _GENAI_AVAILABLE:
        return None

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return None

    _client = genai.Client(api_key=api_key)

    return _client


def is_available():
    """Cek apakah Gemini siap dipakai (library + API key tersedia)."""
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


def generate_text(prompt, max_output_tokens=512, temperature=None):
    """
    Kirim prompt ke Gemini dan kembalikan teks hasil.
    Mengembalikan None jika Gemini tidak tersedia / terjadi error.
    """

    client = _get_client()

    if client is None:
        return None

    try:

        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=prompt,
            config=_build_generation_config(max_output_tokens, temperature)
        )

        if not response.text:
            return None

        return response.text.strip()

    except Exception as e:

        print(f"[Gemini Error] {e}")
        return None


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
