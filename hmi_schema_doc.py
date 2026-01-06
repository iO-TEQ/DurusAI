"""
Compatibility shim for importing `HMI_SCHEMA_DOC`.

Allows both:
- `from hmi_schema_doc import HMI_SCHEMA_DOC`
- `from view_creation.hmi_schema_doc import HMI_SCHEMA_DOC`
"""

try:
    from view_creation.hmi_schema_doc import HMI_SCHEMA_DOC
except Exception as e:
    raise ImportError(
        "Failed to import HMI_SCHEMA_DOC from view_creation.hmi_schema_doc. "
        "Ensure the project root is on PYTHONPATH or run from the repo root."
    ) from e

__all__ = ["HMI_SCHEMA_DOC"]
