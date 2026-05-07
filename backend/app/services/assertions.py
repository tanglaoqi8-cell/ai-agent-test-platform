import json
import re


def run_assertion(assert_type: str, expected_value: str, actual_output: str) -> tuple[bool, str]:
    if assert_type == "contains":
        passed = expected_value in actual_output
        reason = "contains matched" if passed else "expected substring not found"
        return passed, reason

    if assert_type == "regex":
        try:
            passed = re.search(expected_value, actual_output) is not None
            reason = "regex matched" if passed else "regex not matched"
            return passed, reason
        except re.error as exc:
            return False, f"invalid regex: {exc}"

    if assert_type == "json_valid":
        try:
            json.loads(actual_output)
            return True, "valid json"
        except json.JSONDecodeError:
            return False, "output is not valid json"

    return False, f"unsupported assert_type: {assert_type}"
