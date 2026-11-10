"""Only the main branch can publish this repository's single Pages destination."""

from __future__ import annotations

import os
from pathlib import Path


def deploy_target(event: str, ref: str, requested: str = "none") -> str:
    if event == "workflow_dispatch":
        if requested not in {"none", "production"}:
            raise ValueError("Unsupported deploy target; previews are downloadable artifacts")
        if requested == "production" and ref != "refs/heads/main":
            raise ValueError("Pages releases must be built from main")
        return requested
    if event == "push" and ref == "refs/heads/main":
        return "production"
    return "none"


if __name__ == "__main__":
    target = deploy_target(os.environ["GITHUB_EVENT_NAME"], os.environ["GITHUB_REF"],
                           os.environ.get("DEPLOY_TARGET", "none"))
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
        stream.write(f"should_deploy={'true' if target == 'production' else 'false'}\n")
        stream.write(f"deploy_target={target}\n")
    print(f"Resolved deploy_target={target}")
