import json
import re
import socket
import time
from urllib import error, request

from .prompt_executor import _read_api_key

SCORING_TEMPLATE_ID = "default_prompt_score_v0.6"
SCORER_TIMEOUT_SECONDS = 300


def _build_chat_completions_url(base_url):
    return base_url.rstrip("/") + "/chat/completions"


def _build_score_prompt(context):
    return (
        "你是一个严格的Prompt测试评分助手。请基于提供的信息进行评分。"
        "\n你必须只返回JSON对象，不要返回Markdown，不要返回解释文本，不要使用```json代码块。"
        "\n评分维度固定为: relevance, completeness, format_correctness, constraint_following, stability_usability。"
        "\n每个维度分数范围1-5，total_score范围0-100。"
        "\n返回结构必须严格如下："
        '\n{"dimension_scores":{"relevance":1,"completeness":1,"format_correctness":1,"constraint_following":1,"stability_usability":1},"total_score":0,"score_reason":"","problem_points":[],"suggestion":""}'
        "\n上下文如下:\n" + json.dumps(context, ensure_ascii=False)
    )


def _extract_json_text(text):
    stripped = (text or "").strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped, re.IGNORECASE)
    if code_block_match:
        code_content = code_block_match.group(1).strip()
        if code_content.startswith("{") and code_content.endswith("}"):
            return code_content

    first = stripped.find("{")
    last = stripped.rfind("}")
    if first != -1 and last != -1 and first < last:
        return stripped[first : last + 1]

    raise ValueError("json object not found in model output")


def _to_score_number(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value.strip())
    raise ValueError("score value type invalid")


def _normalize_score_payload(parsed):
    if not isinstance(parsed, dict):
        raise ValueError("response root is not object")

    dimension_scores = parsed.get("dimension_scores")
    if not isinstance(dimension_scores, dict):
        raise ValueError("dimension_scores missing or invalid")

    key_map = {
        "relevance": "relevance",
        "相关性": "relevance",
        "completeness": "completeness",
        "完整性": "completeness",
        "format_correctness": "format_correctness",
        "格式正确性": "format_correctness",
        "constraint_following": "constraint_following",
        "约束遵守": "constraint_following",
        "stability_usability": "stability_usability",
        "稳定可用性": "stability_usability",
    }
    required_keys = [
        "relevance",
        "completeness",
        "format_correctness",
        "constraint_following",
        "stability_usability",
    ]

    mapped_scores = {}
    for raw_key, raw_value in dimension_scores.items():
        mapped_key = key_map.get(raw_key)
        if mapped_key:
            mapped_scores[mapped_key] = raw_value

    normalized = {}
    total_5_scale = 0.0
    for key in required_keys:
        if key not in mapped_scores:
            raise ValueError("dimension score missing: {0}".format(key))
        score = _to_score_number(mapped_scores[key])
        if score < 1:
            score = 1.0
        if score > 5:
            score = 5.0
        normalized[key] = score
        total_5_scale += score

    total_score = parsed.get("total_score")
    if isinstance(total_score, (int, float)):
        total_score = float(total_score)
    else:
        total_score = float(round((total_5_scale / 25.0) * 100.0))

    score_reason = parsed.get("score_reason") if isinstance(parsed.get("score_reason"), str) else ""
    suggestion = parsed.get("suggestion") if isinstance(parsed.get("suggestion"), str) else ""
    problem_points = parsed.get("problem_points") if isinstance(parsed.get("problem_points"), list) else []

    return {
        "dimension_scores": normalized,
        "total_score": total_score,
        "score_reason": score_reason,
        "problem_points": problem_points,
        "suggestion": suggestion,
    }


def score_prompt_run(scorer_model_config, score_context):
    start = time.perf_counter()

    api_key = _read_api_key()
    if not api_key:
        return {
            "status": "failed",
            "scoring_template_id": SCORING_TEMPLATE_ID,
            "dimension_scores": None,
            "total_score": None,
            "score_reason": None,
            "problem_points": None,
            "suggestion": None,
            "raw_response": None,
            "error_message": "MODEL_API_KEY_NOT_CONFIGURED",
            "duration_ms": int((time.perf_counter() - start) * 1000),
        }

    if not scorer_model_config.base_url:
        return {
            "status": "failed",
            "scoring_template_id": SCORING_TEMPLATE_ID,
            "dimension_scores": None,
            "total_score": None,
            "score_reason": None,
            "problem_points": None,
            "suggestion": None,
            "raw_response": None,
            "error_message": "MODEL_BASE_URL_NOT_CONFIGURED",
            "duration_ms": int((time.perf_counter() - start) * 1000),
        }

    url = _build_chat_completions_url(scorer_model_config.base_url)
    system_prompt = _build_score_prompt(score_context)
    payload = {
        "model": scorer_model_config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请严格按要求输出JSON评分结果。"},
        ],
        "temperature": scorer_model_config.temperature,
        "top_p": scorer_model_config.top_p,
        "max_tokens": scorer_model_config.max_tokens,
    }

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {0}".format(api_key),
    }

    raw_response = None
    try:
        req = request.Request(url=url, data=body, headers=headers, method="POST")
        with request.urlopen(req, timeout=SCORER_TIMEOUT_SECONDS) as resp:
            raw_response = resp.read().decode("utf-8", errors="replace")

        try:
            parsed = json.loads(raw_response)
            content = parsed["choices"][0]["message"]["content"]
            score_json_text = _extract_json_text(content)
            score_payload = json.loads(score_json_text)
            normalized = _normalize_score_payload(score_payload)
            return {
                "status": "success",
                "scoring_template_id": SCORING_TEMPLATE_ID,
                "dimension_scores": normalized["dimension_scores"],
                "total_score": normalized["total_score"],
                "score_reason": normalized["score_reason"],
                "problem_points": normalized["problem_points"],
                "suggestion": normalized["suggestion"],
                "raw_response": raw_response,
                "error_message": None,
                "duration_ms": int((time.perf_counter() - start) * 1000),
            }
        except Exception as exc:
            return {
                "status": "failed",
                "scoring_template_id": SCORING_TEMPLATE_ID,
                "dimension_scores": None,
                "total_score": None,
                "score_reason": None,
                "problem_points": None,
                "suggestion": None,
                "raw_response": raw_response,
                "error_message": "SCORE_PARSE_ERROR: {0}".format(exc),
                "duration_ms": int((time.perf_counter() - start) * 1000),
            }

    except error.HTTPError as exc:
        try:
            raw_response = exc.read().decode("utf-8", errors="replace")
        except Exception:
            raw_response = str(exc)
        return {
            "status": "failed",
            "scoring_template_id": SCORING_TEMPLATE_ID,
            "dimension_scores": None,
            "total_score": None,
            "score_reason": None,
            "problem_points": None,
            "suggestion": None,
            "raw_response": raw_response,
            "error_message": "HTTP_ERROR: {0} {1}".format(exc.code, raw_response[:500]),
            "duration_ms": int((time.perf_counter() - start) * 1000),
        }
    except (socket.timeout, TimeoutError):
        return {
            "status": "failed",
            "scoring_template_id": SCORING_TEMPLATE_ID,
            "dimension_scores": None,
            "total_score": None,
            "score_reason": None,
            "problem_points": None,
            "suggestion": None,
            "raw_response": raw_response,
            "error_message": "HTTP_ERROR: timeout",
            "duration_ms": int((time.perf_counter() - start) * 1000),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "scoring_template_id": SCORING_TEMPLATE_ID,
            "dimension_scores": None,
            "total_score": None,
            "score_reason": None,
            "problem_points": None,
            "suggestion": None,
            "raw_response": raw_response,
            "error_message": "HTTP_ERROR: {0}".format(exc),
            "duration_ms": int((time.perf_counter() - start) * 1000),
        }
