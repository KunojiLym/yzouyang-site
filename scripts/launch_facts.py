"""Check hand-typed Home identity facts against the public export.

The proof sentence lives only in site.json home_proof_line.text. This module
checks that every number in that sentence appears in the resolved sources.
"""

from __future__ import annotations

import re

_EN_DASH_GAP = " \u2013 "
_INDEXED_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+)(?:\[(\d+)\])?$")
_NUMBER_RE = re.compile(r"\d+")


class _Missing:
    pass


_MISSING = _Missing()


def normalized_experience_title(title: str) -> str:
    """Turn the export's spaced en dash into the comma used on the site."""
    return str(title or "").replace(_EN_DASH_GAP, ", ")


def _experiences(export: dict) -> list[dict]:
    rows = export.get("experiences")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def current_experience(export: dict) -> dict | None:
    rows = _experiences(export)
    for row in rows:
        if not str(row.get("end") or "").strip():
            return row
    return rows[0] if rows else None


def experience_for_record(experience_id: str, export: dict) -> dict | None:
    """Match home_featured.experience_id to an experience id exactly."""
    wanted = str(experience_id or "").strip()
    if not wanted:
        return None
    for row in _experiences(export):
        if str(row.get("id") or "") == wanted:
            return row
    return None


def _step(node: object, token: str) -> object:
    match = _INDEXED_KEY_RE.fullmatch(token)
    if match is None or not isinstance(node, dict):
        return _MISSING
    key = match.group(1)
    if key not in node:
        return _MISSING
    value = node[key]
    index_text = match.group(2)
    if index_text is None:
        return value
    index = int(index_text)
    if not isinstance(value, list) or index < 0 or index >= len(value):
        return _MISSING
    return value[index]


def resolve_source(site: dict, export: dict, path: str) -> object:
    parts = [part for part in str(path or "").split(".") if part]
    if not parts:
        return _MISSING
    for root in (site, export):
        node: object = root
        missing = False
        for part in parts:
            node = _step(node, part)
            if node is _MISSING:
                missing = True
                break
        if not missing:
            return node
    return _MISSING


def _strings(node: object) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, bool) or node is None:
        return []
    if isinstance(node, (int, float)):
        return [str(node)]
    if isinstance(node, dict):
        found: list[str] = []
        for value in node.values():
            found.extend(_strings(value))
        return found
    if isinstance(node, list):
        found = []
        for value in node:
            found.extend(_strings(value))
        return found
    return []


def launch_fact_errors(site: dict, export: dict) -> list[str]:
    errors: list[str] = []
    person = site.get("person") if isinstance(site.get("person"), dict) else {}
    role = current_experience(export)
    if role is None:
        errors.append("export.experiences has no current role to check person.job_title")
    else:
        expected_title = normalized_experience_title(str(role.get("title") or ""))
        job = str(person.get("job_title") or "")
        if job != expected_title:
            errors.append(
                "person.job_title must match the current experience title "
                f"after en-dash normalisation ({job!r} != {expected_title!r})"
            )
        employer = str(person.get("employer") or "")
        organization = str(role.get("organization") or "")
        if employer != organization:
            errors.append(
                "person.employer must match the current experience organization "
                f"exactly ({employer!r} != {organization!r})"
            )

    featured = site.get("home_featured") if isinstance(site.get("home_featured"), dict) else {}
    systems = featured.get("systems") if isinstance(featured.get("systems"), list) else []
    for raw in systems:
        if not isinstance(raw, dict):
            continue
        experience_id = str(raw.get("experience_id") or "").strip()
        card_id = str(raw.get("id") or raw.get("record_id") or "").strip()
        card_employer = str(raw.get("employer") or "")
        if not experience_id:
            errors.append(f"home_featured system {card_id!r} requires experience_id")
            continue
        match = experience_for_record(experience_id, export)
        if match is None:
            errors.append(
                f"home_featured experience_id {experience_id!r} does not match an experience id"
            )
            continue
        organization = str(match.get("organization") or "")
        if card_employer != organization:
            errors.append(
                f"home_featured {card_id!r} employer must match "
                f"{match.get('id')} organization exactly "
                f"({card_employer!r} != {organization!r})"
            )

    proof = site.get("home_proof_line") if isinstance(site.get("home_proof_line"), dict) else {}
    text = str(proof.get("text") or "")
    if not text.strip():
        errors.append("home_proof_line.text is required")
    sources = proof.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("home_proof_line.sources must list at least one site or export path")
        return errors
    source_numbers: list[str] = []
    for path in sources:
        if not isinstance(path, str) or not path.strip():
            errors.append("home_proof_line.sources entries must be non-empty paths")
            continue
        resolved = resolve_source(site, export, path.strip())
        if resolved is _MISSING:
            errors.append(f"home_proof_line source {path!r} does not resolve in site.json or export")
            continue
        source_numbers.extend(_NUMBER_RE.findall("\n".join(_strings(resolved))))
    for number in _NUMBER_RE.findall(text):
        if number not in source_numbers:
            errors.append(
                f"home_proof_line number {number} is not in the resolved source strings"
            )
    return errors
