# Gemini API Setup for Notepad Project

This document explains how to set up the Gemini AI integration in this project so that AI features (the **AI** menu in the notepad, dynamic roasts in the Self Aware Calculator twist) work on each team member's machine.

---

## 1. Install Dependencies

Open a terminal in the project root and run:

```bash
python -m pip install google-genai python-dotenv
```

> If `python` is not recognized, try `py -m pip install ...`

---

## 2. Get a Gemini API Key

1. Go to https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the generated API key (looks like `AQ.Ab8...`)

---

## 3. Create a `.env` File

In the project root (same level as `main.py`), create a new file named **`.env`** with:

```
GEMINI_API_KEY=paste_your_api_key_here
```

⚠️ **Do NOT commit this `.env` file.** Make sure `.env` is listed in `.gitignore`. Each developer should use their own API key — don't share keys or push them to the repo.

---

## 4. Verify the Connection

Run this command in the terminal:

```bash
python -c "from utils.gemini_client import is_available, generate_text; print('Available:', is_available()); print(generate_text('Hello, who are you?'))"
```

**Expected output:**
```
Available: True
<response from Gemini>
```

---

## 5. Troubleshooting

| Issue | Solution |
|---|---|
| `Available: False` | Check that `.env` exists in the project root and is correctly formatted (`GEMINI_API_KEY=...`, no quotes) |
| `ModuleNotFoundError: No module named 'google'` | Run `python -m pip install google-genai` again |
| `ModuleNotFoundError: No module named 'dotenv'` | Run `python -m pip install python-dotenv` |
| `429 RESOURCE_EXHAUSTED` / `limit: 0` error | Your API key has no quota. Create a new key at https://aistudio.google.com/apikey (sometimes a different Google Cloud project is needed) |
| `from google import genai` fails after previously installing `google-generativeai` | Uninstall the old package: `python -m pip uninstall google-generativeai`, then reinstall `google-genai` |

---

## 6. Important Notes

- **AI features are optional.** If `.env` is missing or the API key is invalid, the app still runs normally — the AI menu will show an "AI Feature Unavailable" message, and the Self Aware Calculator twist will use its static fallback roasts instead, with no crash.
- The model used is **`gemini-2.5-flash`** (defined in `utils/gemini_client.py`, variable `_MODEL_NAME`).
- All API call logic lives in a single file: **`utils/gemini_client.py`**. If you need to change the model or add new prompts, edit this file only.

### Using a different / self-hosted API

If you have a different AI HTTP endpoint (self-hosted or another provider), you can configure the project to use it instead of Gemini by adding these to your `.env`:

```
NEW_API_URL=https://your-api.example/v1/generate
NEW_API_KEY=your-api-key-if-needed
```

When `NEW_API_URL` is present, the `utils` package will prefer it and the existing functions (`generate_text()`, `rewrite_text()`, etc.) will delegate to the generic HTTP client. The generic client expects a JSON POST with `prompt` and `max_tokens` fields; adapt `utils/new_api_client.py` if your provider needs a different payload.

---

## 7. Related File Structure

```
project/
├── .env                  <- API key (do not commit, per developer)
├── .gitignore            <- make sure ".env" is listed here
├── main.py
└── utils/
    ├── __init__.py
    └── gemini_client.py  <- all Gemini logic lives here
```