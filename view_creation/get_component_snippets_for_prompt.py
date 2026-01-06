from typing import List


def get_component_snippets_for_prompt(prompt: str, hmi_component_snippets) -> str:
    """
    Return a small concatenated string of relevant component snippets based on the user prompt.
    Keep it small to avoid blowing up context.
    """
    if not hmi_component_snippets:
        return ""

    p = (prompt or "").lower()
    chosen: List[str] = []

    # crude keyword routing – adjust as needed
    def maybe_add(name: str):
        key = name.lower()
        snippet = hmi_component_snippets.get(key)
        if snippet and snippet not in chosen:
            chosen.append(snippet)

    if "button" in p:
        maybe_add("button")

    if "label" in p or "text" in p:
        maybe_add("label")

    if "numeric" in p or "number input" in p or "keypad" in p:
        maybe_add("numericInput")

    if "keyboard" in p:
        maybe_add("keyboard")

    if "nested" in p or "embedded view" in p or "subview" in p:
        maybe_add("nested")

    # You can always add more mappings here

    # Cap to a few snippets so it stays short
    if not chosen:
        return ""
    return "\n\n".join(chosen[:3])
