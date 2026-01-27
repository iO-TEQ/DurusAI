

import os

# Build the system prompt for view creation
# This includes current date/time, rules, and references.

def _read_components_reference() -> str:
    """Read the full HMI components reference text for inclusion in the prompt."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ref_path = os.path.join(base_dir, "..", "ai_reference", "hmi_components_reference.txt")
    try:
        with open(ref_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        # If the reference can't be read, return an empty string to avoid breaking the prompt.
        return ""


def build_system_view_creation_prompt() -> str:
    components_ref = _read_components_reference()

    prompt = (
        "You are an assistant for an HMI/tag editor on the Duro controller.\n"
        "You receive:\n"
        "- A natural-language user request.\n"
        "- A 'context' object may included the current json of the current hmi view and tags.\n"
        "\n"
        "Respond with a single JSON OBJECT (not an array). Keep it concise and focused on changes.\n"
        "The top-level JSON should include these fields; omit any not applicable:\n"
        "In the proposed_changes object, satisfy the user request with minimal additions/updates.\n"
        "{\n"
        '  \"message\": string,\n'
        '  \"steps\": [ { \"title\": string, \"details\": string }, ... ],\n'
        '  \"proposed_changes\": {\n'
        '    \"hmi\": { \"views\": [ ... view objects to add or replace ... ],  "general": { "viewsTree": [ ... ] } },\n'
        '    \"tags_to_add\": { ... tag objects to create ... },\n'
        '   \"component_to_add\": { ... component objects to create or modify ... }\n'
        "  }\n"
        "}\n"
        "\n"
        "Guidelines:\n"
        "- Output only a JSON object (no backticks, no extra text).\n"
        "- Prefer minimal patches: only include views/tags/components that change.\n"
        "- Use fields documented in the schema or examples; avoid arbitrary extras.\n"
        "- Treat device_context.controller_config as current truth for IDs/names.\n"
        "- If a section is not needed, you may omit it or use an empty object/array.\n"
        "- If uncertain, keep changes conservative and explain rationale in 'message'.\n"
        "\n"
        "When you need controller-specific details, rely on:\n"
        "- device_context.controller_config for the current project structure.\n"
        "- device_context.relevant_docs for documentation details (if present in the context).\n"
        "- device_context.component_reference for the exact shapes of relevant component types\n"
        "  (label, button, numericInput, keyboard, nested view, etc.). \n"
        "\n"
    )

    return prompt

