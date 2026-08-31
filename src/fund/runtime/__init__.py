"""Deterministic money-path package protected by axiom A1.

This namespace may contain risk, execution, reconciliation, and allocation code
only.  Import Linter and the independent AST contract forbid direct and
transitive access to model SDKs, generic network clients, and local inference
clients.
"""

from .guard import ModelCredentialError, assert_no_model_credentials

__all__ = ["ModelCredentialError", "assert_no_model_credentials"]
