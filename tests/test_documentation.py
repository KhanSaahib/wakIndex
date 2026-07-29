"""Description: Documentation regression tests for local links and copyable policy examples."""

import re
import tomllib
from pathlib import Path

from wakindex.policy import Policy

ROOT = Path(__file__).parents[1]
LOCAL_LINK = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)#]+)(?:#[^)]+)?\)")


def test_documentation_local_links_resolve() -> None:
    documents = [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "RELEASE.md",
        *(ROOT / "docs").glob("*.md"),
    ]

    for document in documents:
        for target in LOCAL_LINK.findall(document.read_text(encoding="utf-8")):
            resolved = (document.parent / target).resolve()
            assert resolved.exists(), f"{document.relative_to(ROOT)} links to missing {target}"


def test_copyable_policy_examples_are_valid() -> None:
    for policy_path in sorted((ROOT / "examples").glob("*-policy.toml")):
        policy = Policy.load(policy_path)
        assert policy.version == 1
        assert policy.default == "deny"


def test_enterprise_account_catalog_example_is_valid_toml() -> None:
    with (ROOT / "examples" / "enterprise-accounts.toml").open("rb") as stream:
        catalog = tomllib.load(stream)

    assert catalog["version"] == 1
    assert catalog["organization"]["name"] == "Example Corporation"
    assert {account["kind"] for account in catalog["accounts"]} == {"human", "service"}
