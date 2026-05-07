import json
import os
import socket
import time
from urllib import error, request

API_KEY_ENV_CANDIDATES = [
    "AI_TEST_MODEL_API_KEY",
    "OPENAI_API_KEY",
    "DASHSCOPE_API_KEY",
]


def _read_api_key():
    for env_name in API_KEY_ENV_CANDIDATES:
        value = os.environ.get(env_name)
        if value:
            return value
    return None


def _build_chat_completions_url(base_url):
    return base_url.rstrip("/") + "/chat/completions"


def execute_prompt_once(rendered_prompt, user_input_text, model_config):
    start = time.perf_counter()

    api_key = _read_api_key()
    if not api_key:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return {
            "status": "failed",
            "actual_output": "MODEL_API_KEY_NOT_CONFIGURED",
            "raw_response": None,
            "error_message": "MODEL_API_KEY_NOT_CONFIGURED",
            "duration_ms": duration_ms,
        }

    if not model_config.base_url:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return {
            "status": "failed",
            "actual_output": "MODEL_BASE_URL_NOT_CONFIGURED",
            "raw_response": None,
            "error_message": "MODEL_BASE_URL_NOT_CONFIGURED",
            "duration_ms": duration_ms,
        }

    url = _build_chat_completions_url(model_config.base_url)
    payload = {
        "model": model_config.model,
        "messages": [
            {"role": "system", "content": rendered_prompt},
            {"role": "user", "content": user_input_text},
        ],
        "temperature": model_config.temperature,
        "top_p": model_config.top_p,
        "max_tokens": model_config.max_tokens,
    }

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {0}".format(api_key),
    }

    raw_response = None
    try:
        req = request.Request(url=url, data=body, headers=headers, method="POST")
        with request.urlopen(req, timeout=60) as resp:
            raw_response = resp.read().decode("utf-8", errors="replace")

        try:
            parsed = json.loads(raw_response)
            actual_output = parsed["choices"][0]["message"]["content"]
            error_message = None
            status = "success"
        except Exception as exc:
            actual_output = raw_response
            error_message = "RESPONSE_PARSE_ERROR: {0}".format(exc)
            status = "failed"

        duration_ms = int((time.perf_counter() - start) * 1000)
        return {
            "status": status,
            "actual_output": actual_output,
            "raw_response": raw_response,
            "error_message": error_message,
            "duration_ms": duration_ms,
        }

    except error.HTTPError as exc:
        try:
            raw_response = exc.read().decode("utf-8", errors="replace")
        except Exception:
            raw_response = str(exc)
        duration_ms = int((time.perf_counter() - start) * 1000)
        return {
            "status": "failed",
            "actual_output": raw_response,
            "raw_response": raw_response,
            "error_message": "HTTP_ERROR: {0} {1}".format(exc.code, raw_response[:500]),
            "duration_ms": duration_ms,
        }
    except (socket.timeout, TimeoutError):
        duration_ms = int((time.perf_counter() - start) * 1000)
        return {
            "status": "failed",
            "actual_output": "HTTP_ERROR: timeout",
            "raw_response": raw_response,
            "error_message": "HTTP_ERROR: timeout",
            "duration_ms": duration_ms,
        }
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return {
            "status": "failed",
            "actual_output": "HTTP_ERROR: {0}".format(exc),
            "raw_response": raw_response,
            "error_message": "HTTP_ERROR: {0}".format(exc),
            "duration_ms": duration_ms,
        }
