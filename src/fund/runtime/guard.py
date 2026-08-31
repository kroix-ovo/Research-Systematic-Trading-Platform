"""Runtime startup guard for A1 credential separation."""

from __future__ import annotations

from collections.abc import Mapping
import os


MODEL_CREDENTIAL_NAMES = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "COHERE_API_KEY",
        "DEEPSEEK_API_KEY",
        "GOOGLE_API_KEY",
        "HF_TOKEN",
        "HUGGINGFACE_TOKEN",
        "MISTRAL_API_KEY",
        "OPENAI_API_KEY",
        "TOGETHER_API_KEY",
    }
)


class ModelCredentialError(RuntimeError):
    """Raised when a model credential is visible to the money-path process."""


def assert_no_model_credentials(
    environment: Mapping[str, str] | None = None,
) -> None:
    """Refuse runtime startup when any known model credential is present."""

    values = os.environ if environment is None else environment
    exposed = sorted(name for name in MODEL_CREDENTIAL_NAMES if values.get(name))
    if exposed:
        raise ModelCredentialError(
            f"model credentials are forbidden in the runtime environment: {exposed}"
        )
