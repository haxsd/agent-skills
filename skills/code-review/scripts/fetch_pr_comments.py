#!/usr/bin/env python3
"""
Fetch all PR conversation comments + reviews + review threads (inline threads)
for a PR (default: the PR of the current git branch) via read-only `gh api graphql`.

Derived from openai/skills skills/.curated/gh-address-comments/scripts/fetch_comments.py
(commit 49f948faa9258a0c61caceaf225e179651397431), Copyright OpenAI, Apache-2.0.
Modified by agent-skills contributors (2026): --pr/--repo arguments, PRs are
resolved in the base repository (fork PRs previously queried the head fork),
finished pagination cursors are no longer re-fetched (duplicate nodes), UTF-8
I/O, --unresolved filter. See ../NOTICE.txt and ../LICENSES/Apache-2.0.txt.

Usage:
  python fetch_pr_comments.py [--pr 123] [--repo owner/name] [--unresolved] > pr_comments.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Any

QUERY = """\
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $commentsCursor: String,
  $reviewsCursor: String,
  $threadsCursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      url
      title
      state

      # Top-level "Conversation" comments (issue comments on the PR)
      comments(first: 100, after: $commentsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          body
          createdAt
          updatedAt
          author { login }
        }
      }

      # Review submissions (Approve / Request changes / Comment), with body if present
      reviews(first: 100, after: $reviewsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          state
          body
          submittedAt
          author { login }
        }
      }

      # Inline review threads (grouped), includes resolved state
      reviewThreads(first: 100, after: $threadsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          diffSide
          startLine
          startDiffSide
          originalLine
          originalStartLine
          resolvedBy { login }
          comments(first: 100) {
            nodes {
              id
              body
              createdAt
              updatedAt
              author { login }
            }
          }
        }
      }
    }
  }
}
"""


def _run(cmd: list[str], stdin: str | None = None) -> str:
    p = subprocess.run(cmd, input=stdin, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr}")
    return p.stdout


def _run_json(cmd: list[str], stdin: str | None = None) -> dict[str, Any]:
    out = _run(cmd, stdin=stdin)
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON from command output: {e}\nRaw:\n{out}") from e


def _ensure_gh_authenticated() -> None:
    try:
        _run(["gh", "auth", "status"])
    except RuntimeError:
        print("run `gh auth login` to authenticate the GitHub CLI", file=sys.stderr)
        raise RuntimeError("gh auth status failed; run `gh auth login` to authenticate the GitHub CLI") from None


def gh_pr_view_json(fields: str) -> dict[str, Any]:
    # fields is a comma-separated list like: "number,headRepositoryOwner,headRepository"
    return _run_json(["gh", "pr", "view", "--json", fields])


def get_pr_ref(pr_value: str | None, repo_value: str | None) -> tuple[str, str, int]:
    """
    Resolve owner/repo/number of the PR. The PR number belongs to the base
    repository, so owner/repo come from the PR URL, not from the head fork.
    """
    cmd = ["gh", "pr", "view"]
    if pr_value:
        cmd.append(pr_value)
    if repo_value:
        cmd += ["--repo", repo_value]
    pr = _run_json(cmd + ["--json", "number,url"])
    match = re.match(r"https://[^/]+/([^/]+)/([^/]+)/pull/(\d+)", pr["url"])
    if not match:
        raise RuntimeError(f"Unexpected PR URL: {pr['url']}")
    return match.group(1), match.group(2), int(match.group(3))


def gh_api_graphql(
    owner: str,
    repo: str,
    number: int,
    comments_cursor: str | None = None,
    reviews_cursor: str | None = None,
    threads_cursor: str | None = None,
) -> dict[str, Any]:
    """
    Call `gh api graphql` using -F variables, avoiding JSON blobs with nulls.
    Query is passed via stdin using query=@- to avoid shell newline/quoting issues.
    """
    cmd = [
        "gh",
        "api",
        "graphql",
        "-F",
        "query=@-",
        "-F",
        f"owner={owner}",
        "-F",
        f"repo={repo}",
        "-F",
        f"number={number}",
    ]
    if comments_cursor:
        cmd += ["-F", f"commentsCursor={comments_cursor}"]
    if reviews_cursor:
        cmd += ["-F", f"reviewsCursor={reviews_cursor}"]
    if threads_cursor:
        cmd += ["-F", f"threadsCursor={threads_cursor}"]

    return _run_json(cmd, stdin=QUERY)


def fetch_all(owner: str, repo: str, number: int) -> dict[str, Any]:
    conversation_comments: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    review_threads: list[dict[str, Any]] = []

    comments_cursor: str | None = None
    reviews_cursor: str | None = None
    threads_cursor: str | None = None

    pr_meta: dict[str, Any] | None = None
    # A finished connection must not be queried again with a null cursor, or its
    # first page would be appended a second time.
    done = {"comments": False, "reviews": False, "threads": False}

    while True:
        payload = gh_api_graphql(
            owner=owner,
            repo=repo,
            number=number,
            comments_cursor=comments_cursor,
            reviews_cursor=reviews_cursor,
            threads_cursor=threads_cursor,
        )

        if "errors" in payload and payload["errors"]:
            raise RuntimeError(f"GitHub GraphQL errors:\n{json.dumps(payload['errors'], indent=2)}")

        pr = payload["data"]["repository"]["pullRequest"]
        if pr_meta is None:
            pr_meta = {
                "number": pr["number"],
                "url": pr["url"],
                "title": pr["title"],
                "state": pr["state"],
                "owner": owner,
                "repo": repo,
            }

        c = pr["comments"]
        r = pr["reviews"]
        t = pr["reviewThreads"]

        if not done["comments"]:
            conversation_comments.extend(c.get("nodes") or [])
            comments_cursor = c["pageInfo"]["endCursor"] if c["pageInfo"]["hasNextPage"] else None
            done["comments"] = comments_cursor is None
        if not done["reviews"]:
            reviews.extend(r.get("nodes") or [])
            reviews_cursor = r["pageInfo"]["endCursor"] if r["pageInfo"]["hasNextPage"] else None
            done["reviews"] = reviews_cursor is None
        if not done["threads"]:
            review_threads.extend(t.get("nodes") or [])
            threads_cursor = t["pageInfo"]["endCursor"] if t["pageInfo"]["hasNextPage"] else None
            done["threads"] = threads_cursor is None

        if all(done.values()):
            break

    assert pr_meta is not None
    return {
        "pull_request": pr_meta,
        "conversation_comments": conversation_comments,
        "reviews": reviews,
        "review_threads": review_threads,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch PR comments, reviews and review threads (read-only).")
    parser.add_argument("--pr", help="PR number or URL (default: PR of the current branch)")
    parser.add_argument("--repo", help="owner/name when not running inside the repository")
    parser.add_argument("--unresolved", action="store_true",
                        help="keep only review threads that are neither resolved nor outdated")
    args = parser.parse_args()
    _ensure_gh_authenticated()
    owner, repo, number = get_pr_ref(args.pr, args.repo)
    result = fetch_all(owner, repo, number)
    if args.unresolved:
        result["review_threads"] = [
            t for t in result["review_threads"] if not t.get("isResolved") and not t.get("isOutdated")
        ]
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
