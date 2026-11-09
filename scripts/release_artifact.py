"""Bind the uploaded site tree to its CI revision and file hashes."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path


def release_manifest(root: Path, *, revision: str, ref: str, run_id: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("A full Git commit SHA is required")
    if not (root / "index.html").is_file():
        raise ValueError("Build the site before recording a release")
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Release artifacts cannot contain symlinks")
        if not path.is_file() or path == root / "release.json":
            continue
        files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"schema_version": 1, "revision": revision, "ref": ref, "run_id": run_id, "files": files}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "dist"
    manifest = release_manifest(root, revision=os.environ["GITHUB_SHA"],
                                ref=os.environ["GITHUB_REF"], run_id=os.environ["GITHUB_RUN_ID"])
    (root / "release.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {len(manifest['files'])} files for {manifest['revision']}")
