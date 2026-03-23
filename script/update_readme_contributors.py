#!/usr/bin/env python3
"""Regenerate README contributors block (small overlapping avatars)."""
from __future__ import annotations

import html
import json
import os
import re
import urllib.error
import urllib.request

AVATAR_SIZE = 28
OVERLAP = "-0.35em"


def fetch_contributors(repo: str, token: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/contributors?per_page=100"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "heycoder-readme-contributors",
        },
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return [c for c in data if not str(c.get("login", "")).endswith("[bot]")]


def avatar_src(avatar_url: str) -> str:
    sep = "&" if "?" in avatar_url else "?"
    return f"{avatar_url}{sep}s=64"


def build_block(contribs: list[dict]) -> str:
    lines = [
        '<p align="left">',
        '<span style="display:inline-flex;align-items:center;flex-wrap:wrap;">',
    ]
    for i, c in enumerate(contribs):
        login = c["login"]
        profile = html.escape(f"https://github.com/{login}", quote=True)
        src = html.escape(avatar_src(c["avatar_url"]), quote=True)
        login_e = html.escape(login, quote=True)
        ml = "0" if i == 0 else OVERLAP
        lines.append(
            f'<a href="{profile}" title="{login_e}">'
            f'<img src="{src}" width="{AVATAR_SIZE}" height="{AVATAR_SIZE}" alt="{login_e}" '
            f'style="border-radius:50%;border:2px solid #fff;margin-left:{ml};vertical-align:middle;box-sizing:content-box;" />'
            f"</a>"
        )
    lines.append("</span>")
    lines.append("</p>")
    return "\n".join(lines)


def main() -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "tageecc/heycoder")
    token = os.environ.get("GITHUB_TOKEN", "")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(root, "README.md")
    with open(readme_path, encoding="utf-8") as f:
        text = f.read()
    try:
        contribs = fetch_contributors(repo, token)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"GitHub API error: {e}") from e
    block = build_block(contribs)
    pattern = r"(<!-- readme: contributors -start -->)\s*[\s\S]*?\s*(<!-- readme: contributors -end -->)"
    repl = rf"\1\n{block}\n\2"
    new_text, n = re.subn(pattern, repl, text, count=1)
    if n != 1:
        raise SystemExit("contributors markers not found in README.md")
    if new_text == text:
        print("contributors block unchanged")
        return
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("README.md updated")


if __name__ == "__main__":
    main()
