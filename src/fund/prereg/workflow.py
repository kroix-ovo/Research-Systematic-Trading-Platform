"""Git-backed immutable pre-registration workflow.

The freeze operation commits only the requested pre-registration path and uses
the document's explicit UTC timestamp for Git author, committer, and tagger
dates.  That removes wall-clock input from the freeze itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess


class PreregistrationValidationError(ValueError):
    """Raised when a pre-registration is incomplete or still has placeholders."""


class FrozenPreregistrationError(RuntimeError):
    """Raised when a frozen pre-registration has changed or is not tagged."""


_HEADINGS = tuple(f"## {number}." for number in range(1, 10))
_LABELS = (
    "H1 (one sentence, falsifiable)",
    "Mechanism (why it should be true, 3 links)",
    "Prior belief it is true, before looking (a number, 0-1)",
    "Instrument",
    "Vendor",
    "Sample start/end",
    "Point-in-time method",
    "What I will do about restatement bias",
    "Estimators to be tried (EXHAUSTIVE LIST — anything added later is an amendment)",
    "Parameter grids (EXHAUSTIVE)",
    "Implied trial count N",
    "Rebalancing frequency",
    "Execution assumption",
    "Volatility target sigma*",
    "Leverage cap L",
    "Spread",
    "Commission",
    "Impact",
    "Financing (long AND short of 1x)",
    "Sensitivity levels to be reported",
    "B1",
    "B2",
    "B3",
    "Comparison metric (scale-free AND matched-volatility)",
    "Walk-forward scheme",
    "Purge length",
    "Embargo length",
    "Deflation method and where N comes from",
    "Significance test vs baseline",
    "Robustness: leave-one-crisis-out periods",
    "I will abandon this slice if",
    "I will NOT do the following to rescue a negative result",
    "If the result is positive, the most likely non-edge explanation is",
    "If negative, what I would want to test next",
)
_THRESHOLDS = (
    r"DSR\s*>\s*(\d+(?:\.\d+)?)",
    r"PBO 95% upper bound\s*<\s*(\d+(?:\.\d+)?)",
    r"LW Sharpe-difference p\s*<\s*(\d+(?:\.\d+)?)\s+vs B3",
    r"Survives\s*(\d+(?:\.\d+)?)x cost sensitivity",
    r"cap_binding_fraction\s*<\s*(\d+(?:\.\d+)?)",
)
_PLACEHOLDER = re.compile(r"(?i)(?:\bTBD\b|\bTODO\b|_{2,}|\?{2,}|<UTC timestamp>)")


@dataclass(frozen=True)
class ValidationResult:
    frozen_timestamp: str
    tag: str


def _field_value(text: str, label: str) -> str | None:
    labels = "|".join(re.escape(candidate) for candidate in _LABELS)
    pattern = re.compile(
        rf"(?m){re.escape(label)}\s*:\s*(.*?)(?=(?:{labels})\s*:|$)"
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def validate(path: str | os.PathLike[str]) -> ValidationResult:
    """Validate every field in the charter's section 5 template."""

    prereg = Path(path)
    text = prereg.read_text(encoding="utf-8")
    errors: list[str] = []
    for heading in _HEADINGS:
        if heading not in text:
            errors.append(f"missing section heading: {heading}")
    if _PLACEHOLDER.search(text):
        errors.append("document contains TBD/TODO/blank placeholder text")
    for label in _LABELS:
        value = _field_value(text, label)
        if value is None:
            errors.append(f"missing field: {label}")
        elif not value:
            errors.append(f"empty field: {label}")
    for threshold in _THRESHOLDS:
        if not re.search(threshold, text):
            errors.append(f"missing numeric threshold matching: {threshold}")

    frozen_match = re.search(
        r"(?m)^Frozen:\s*(\S+)\s+Git tag:\s*(\S+)\s*$", text
    )
    if not frozen_match:
        errors.append("missing 'Frozen: <UTC timestamp>   Git tag: <tag>' header")
        frozen_timestamp, tag = "", ""
    else:
        frozen_timestamp, tag = frozen_match.groups()
        try:
            parsed = datetime.fromisoformat(frozen_timestamp.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
                raise ValueError
        except ValueError:
            errors.append("Frozen timestamp must be an ISO-8601 UTC timestamp")
    if errors:
        raise PreregistrationValidationError("; ".join(errors))
    return ValidationResult(frozen_timestamp=frozen_timestamp, tag=tag)


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    command = ["git", *args]
    completed = subprocess.run(
        command,
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise FrozenPreregistrationError(f"{' '.join(command)} failed: {detail}")
    return completed.stdout.strip()


def _repo_and_relative(path: Path) -> tuple[Path, str]:
    absolute = path.resolve()
    repo = Path(_git(path.parent, "rev-parse", "--show-toplevel")).resolve()
    try:
        relative = str(absolute.relative_to(repo))
    except ValueError as exc:
        raise FrozenPreregistrationError("pre-registration must be inside its Git repository") from exc
    return repo, relative


def freeze(path: str | os.PathLike[str]) -> str:
    """Validate, commit, and annotate-tag a new pre-registration.

    The returned value is the annotated tag object's SHA, matching
    ``git rev-parse <tag>``.  Existing history or an existing tag is refused;
    freezing is a one-way human gate, not an update operation.
    """

    prereg = Path(path)
    validation = validate(prereg)
    repo, relative = _repo_and_relative(prereg)
    if _git(repo, "log", "--all", "--format=%H", "--", relative):
        raise FrozenPreregistrationError("pre-registration already has Git history")
    tag_exists = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{validation.tag}"],
        cwd=repo,
        check=False,
    ).returncode == 0
    if tag_exists:
        raise FrozenPreregistrationError(f"tag already exists: {validation.tag}")

    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_DATE": validation.frozen_timestamp,
            "GIT_COMMITTER_DATE": validation.frozen_timestamp,
        }
    )
    _git(repo, "add", "--", relative, env=env)
    _git(
        repo,
        "commit",
        "--only",
        "-m",
        f"prereg: {prereg.parent.name} frozen before data load",
        "--",
        relative,
        env=env,
    )
    _git(
        repo,
        "tag",
        "-a",
        validation.tag,
        "-m",
        f"frozen {validation.frozen_timestamp}",
        env=env,
    )
    return _git(repo, "rev-parse", validation.tag)


def verify_frozen(path: str | os.PathLike[str]) -> str:
    """Return the tag hash if the path is tagged and has never been modified."""

    prereg = Path(path)
    validation = validate(prereg)
    repo, relative = _repo_and_relative(prereg)
    tag_hash = _git(repo, "rev-parse", "--verify", f"refs/tags/{validation.tag}")
    if _git(repo, "status", "--porcelain", "--", relative):
        raise FrozenPreregistrationError("pre-registration differs from its committed version")
    modifications = _git(
        repo,
        "log",
        "--diff-filter=M",
        "--format=%H",
        "--",
        relative,
    )
    if modifications:
        raise FrozenPreregistrationError(
            "pre-registration has a modification commit; frozen text is immutable"
        )
    tagged_text = _git(repo, "show", f"{validation.tag}:{relative}")
    if tagged_text.rstrip("\n") != prereg.read_text(encoding="utf-8").rstrip("\n"):
        raise FrozenPreregistrationError("working file does not match the frozen tag")
    return tag_hash
