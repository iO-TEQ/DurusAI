
from urllib.parse import urlparse, urlunparse


def _llm_models_url(url) -> str:
    """Return the /v1/models URL derived from LLM_API_URL host/port."""
    u = urlparse(url)
    return urlunparse((u.scheme, u.netloc, "/v1/models", "", "", ""))
