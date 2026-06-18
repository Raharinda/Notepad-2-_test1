"""Generic wrapper for a simple HTTP-based AI API.

This client is intentionally minimal and provider-agnostic. It expects the
API to accept a JSON POST with keys like `prompt`, `max_tokens` and
`temperature`, and to return either plain text or a JSON body containing
the generated text in a key such as `text`, `result`, or `output`.

Environment variables can be used to configure retry behavior:
- `NEW_API_MAX_RETRIES`, `NEW_API_BACKOFF_BASE`, `NEW_API_BACKOFF_JITTER`

If your new API has a different payload shape, adapt `generate_text()` to
match the provider's required format.
"""

import os
import time
import random
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


_DEFAULT_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0
_BACKOFF_JITTER = 0.5


def generate_text(url, api_key, prompt, max_output_tokens=512, temperature=None):
    """Send `prompt` to `url` and return generated text, or None on failure.

    This function is defensive: it will try to parse JSON responses that
    contain a plausible text field, or return the raw body otherwise.
    """

    if not url:
        return None

    try:
        max_attempts = int(os.environ.get("NEW_API_MAX_RETRIES", _DEFAULT_MAX_RETRIES))
    except Exception:
        max_attempts = _DEFAULT_MAX_RETRIES

    try:
        backoff_base = float(os.environ.get("NEW_API_BACKOFF_BASE", _BACKOFF_BASE))
    except Exception:
        backoff_base = _BACKOFF_BASE

    try:
        backoff_jitter = float(os.environ.get("NEW_API_BACKOFF_JITTER", _BACKOFF_JITTER))
    except Exception:
        backoff_jitter = _BACKOFF_JITTER

    payload = {
        "prompt": prompt,
        "max_tokens": max_output_tokens,
    }

    if temperature is not None:
        payload["temperature"] = temperature

    data = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain",
    }

    if api_key:
        # Prefer Authorization bearer token, fallback to X-API-Key
        headers["Authorization"] = f"Bearer {api_key}"

    for attempt in range(max_attempts):
        try:
            req = Request(url, data=data, headers=headers, method="POST")
            with urlopen(req, timeout=30) as resp:
                body = resp.read()
                try:
                    j = json.loads(body.decode("utf-8"))
                    # common keys
                    for k in ("text", "result", "output", "generated_text"):
                        if k in j and isinstance(j[k], str):
                            return j[k].strip()
                    # try nested structures
                    if isinstance(j.get("choices"), list) and j["choices"]:
                        c0 = j["choices"][0]
                        if isinstance(c0, dict) and "text" in c0:
                            return c0["text"].strip()
                    # fallback: stringify entire JSON
                    return json.dumps(j)

                except Exception:
                    # not JSON, return raw text
                    try:
                        return body.decode("utf-8").strip()
                    except Exception:
                        return None

        except (HTTPError, URLError, TimeoutError) as e:
            last = (attempt == max_attempts - 1)
            if last:
                print(f"[NewAPI Error] {e}")
                return None

            backoff = backoff_base * (2 ** attempt) + random.uniform(0, backoff_jitter)
            time.sleep(backoff)
            continue

        except Exception as e:
            # Catch-all for unexpected errors
            print(f"[NewAPI Error] {e}")
            return None

    return None
