def sanitize_llm_json(text: str) -> str:
    """
    Strip control tokens and extract the largest {...} block.
    """
    for tok in ("<|eot_id|>", "<|eom_id|>"):
        text = text.replace(tok, "")
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object delimiters found in LLM output")

    json_str = text[start:end + 1]
    return json_str
