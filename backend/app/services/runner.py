import json
from urllib import error, parse, request

from ..models import TestTarget


def _build_headers(headers_json):
    default_headers = {"Content-Type": "application/json"}
    if not headers_json:
        return default_headers
    try:
        parsed = json.loads(headers_json)
    except Exception as exc:
        return {"__error__": "HTTP_ERROR: invalid headers_json: {0}".format(exc)}
    if not isinstance(parsed, dict):
        return {"__error__": "HTTP_ERROR: headers_json must be a JSON object"}
    return parsed


def _build_body(body_template, input_text):
    template = body_template if body_template else '{"input_text":"{input_text}"}'
    return template.replace("{input_text}", input_text)


def _read_response(resp):
    return resp.read().decode("utf-8", errors="replace")


def _append_get_query(endpoint_url, input_text):
    query = parse.urlencode({"input_text": input_text})
    if "?" in endpoint_url:
        return "{0}&{1}".format(endpoint_url, query)
    return "{0}?{1}".format(endpoint_url, query)


def _post_http(endpoint_url, headers_json, body_template, input_text):
    headers = _build_headers(headers_json)
    if "__error__" in headers:
        return headers["__error__"]

    body_text = _build_body(body_template, input_text)
    body_bytes = body_text.encode("utf-8")

    try:
        req = request.Request(
            url=endpoint_url,
            data=body_bytes,
            headers=headers,
            method="POST",
        )
        with request.urlopen(req, timeout=30) as resp:
            return _read_response(resp)
    except error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            detail = str(exc)
        return "HTTP_ERROR: {0} {1}".format(exc, detail)
    except Exception as exc:
        return "HTTP_ERROR: {0}".format(exc)


def _get_http(endpoint_url, headers_json, input_text):
    headers = _build_headers(headers_json)
    if "__error__" in headers:
        return headers["__error__"]

    url = _append_get_query(endpoint_url, input_text)
    try:
        req = request.Request(
            url=url,
            headers=headers,
            method="GET",
        )
        with request.urlopen(req, timeout=30) as resp:
            return _read_response(resp)
    except error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            detail = str(exc)
        return "HTTP_ERROR: {0} {1}".format(exc, detail)
    except Exception as exc:
        return "HTTP_ERROR: {0}".format(exc)


def _run_http_target(target, input_text):
    method = (target.method or "POST").upper()
    if method == "POST":
        return _post_http(target.endpoint_url, target.headers_json, target.body_template, input_text)
    if method == "GET":
        return _get_http(target.endpoint_url, target.headers_json, input_text)
    return "HTTP_ERROR: unsupported method: {0}".format(method)


def run_target(target: TestTarget, input_text: str) -> str:
    if target.target_type == "prompt":
        return f"MockPromptResponse: {input_text}"

    if target.target_type == "agent_http":
        if target.endpoint_url:
            return _run_http_target(target, input_text)
        return f"MockAgentResponse: {input_text}"

    if target.target_type == "rag_http":
        if target.endpoint_url:
            return _run_http_target(target, input_text)
        return f"MockRagResponse: {input_text}"

    raise ValueError(f"Unsupported target_type: {target.target_type}")
