import json
import re

PLACEHOLDER_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _to_text(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def render_prompt(prompt_content, input_text=None, input_variables=None):
    variables = {}
    if isinstance(input_variables, dict):
        variables.update(input_variables)
    if input_text is not None and input_text != "":
        variables["input_text"] = input_text

    placeholders = PLACEHOLDER_PATTERN.findall(prompt_content)
    missing = [name for name in placeholders if name not in variables]

    rendered_prompt = prompt_content
    if placeholders:
        for name in set(placeholders):
            if name in variables:
                rendered_prompt = rendered_prompt.replace("{" + name + "}", _to_text(variables[name]))

    if input_text is not None and input_text != "":
        user_message_text = input_text
    else:
        user_message_text = json.dumps(input_variables or {}, ensure_ascii=False)

    return {
        "rendered_prompt": rendered_prompt,
        "input_variables_json": json.dumps(input_variables, ensure_ascii=False) if isinstance(input_variables, dict) else None,
        "missing_variables": missing,
        "user_message_text": user_message_text,
    }
