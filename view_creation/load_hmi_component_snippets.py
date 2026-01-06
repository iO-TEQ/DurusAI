import os
from typing import Dict, List, Optional

# Load HMI component snippets from hmi_components_reference.txt
def _load_hmi_component_snippets(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        print(f"[AGENT DEBUG] hmi_components_reference.txt not found at: {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    lines = text.splitlines()
    snippets: Dict[str, List[str]] = {}
    current_name: Optional[str] = None
    current_block: List[str] = []

    for line in lines:
        if line.strip().startswith("COMPONENT:"):
            # Save previous block
            if current_name and current_block:
                snippets[current_name] = "\n".join(current_block).strip()
            # Start new block
            current_name = line.split("COMPONENT:", 1)[1].strip().split()[0]
            current_name = current_name.strip().lower()
            current_block = [line]
        else:
            if current_name is not None:
                current_block.append(line)

    # Save last block
    if current_name and current_block:
        snippets[current_name] = "\n".join(current_block).strip()

    print(f"[AGENT DEBUG] Loaded HMI component snippets: {list(snippets.keys())}")
    return snippets