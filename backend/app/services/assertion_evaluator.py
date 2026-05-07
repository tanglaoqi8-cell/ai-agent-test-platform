import json
import re


def evaluate_assertion(assert_type, expected_value, actual_output):
    if assert_type == "contains":
        passed = expected_value in actual_output
        if passed:
            return {
                "assertion_status": "passed",
                "assertion_passed": True,
                "assertion_reason": "contains assertion passed",
            }
        return {
            "assertion_status": "failed",
            "assertion_passed": False,
            "assertion_reason": "contains assertion failed: expected text not found",
        }

    if assert_type == "regex":
        try:
            matched = re.search(expected_value, actual_output) is not None
        except re.error as exc:
            return {
                "assertion_status": "failed",
                "assertion_passed": False,
                "assertion_reason": "regex assertion error: {0}".format(exc),
            }

        if matched:
            return {
                "assertion_status": "passed",
                "assertion_passed": True,
                "assertion_reason": "regex assertion passed",
            }
        return {
            "assertion_status": "failed",
            "assertion_passed": False,
            "assertion_reason": "regex assertion failed: pattern not matched",
        }

    if assert_type == "json_valid":
        try:
            json.loads(actual_output)
            return {
                "assertion_status": "passed",
                "assertion_passed": True,
                "assertion_reason": "json_valid assertion passed",
            }
        except Exception:
            return {
                "assertion_status": "failed",
                "assertion_passed": False,
                "assertion_reason": "json_valid assertion failed: invalid json",
            }

    return {
        "assertion_status": "failed",
        "assertion_passed": False,
        "assertion_reason": "unsupported assert_type",
    }
