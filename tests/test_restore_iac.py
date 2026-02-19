import pytest
from pathlib import Path
from textwrap import dedent

try:
    from restore_iac import (
        GITHUB_URL_RE,
        RepoURL,
        collect_iac_files,
        deduplicate_preserve_order,
        extract_repo_urls_from_csv,
        is_iac_file,
    )
except ImportError:
    pytest.skip("restore_iac module not available", allow_module_level=True)


def test_github_url_regex_matches_owner_repo():
    m = GITHUB_URL_RE.search("https://github.com/org-name/repo_name")
    assert m
    assert m.group("owner") == "org-name"
    assert m.group("repo") == "repo_name"


def test_repo_url_properties():
    r = RepoURL("owner", "my.repo")
    assert r.https_url == "https://github.com/owner/my.repo.git"
    assert r.safe_dirname == "owner_my.repo"


def test_deduplicate_preserve_order():
    urls = [
        RepoURL("a", "one"),
        RepoURL("b", "two"),
        RepoURL("a", "one"),
    ]
    deduped = deduplicate_preserve_order(urls)
    assert deduped == [RepoURL("a", "one"), RepoURL("b", "two")]


def test_extract_repo_urls_from_csv(tmp_path: Path):
    csv_content = dedent(
        """\
        id,url,other
        1,https://github.com/org1/repo1,foo
        2,https://api.github.com/repos/org2/repo2,ignore
        3,https://github.com/org2/repo2.git,bar
        4,not-a-url,baz
        """
    )
    csv_path = tmp_path / "repositories.csv"
    csv_path.write_text(csv_content, encoding="utf-8")

    urls = extract_repo_urls_from_csv(csv_path)
    assert RepoURL("org1", "repo1") in urls
    assert RepoURL("org2", "repo2") in urls
    # api.github.com should be ignored
    assert all("api.github.com" not in u.https_url for u in urls)


def test_is_iac_file_and_collect_iac_files(tmp_path: Path):
    # create some files with IaC and non-IaC extensions
    iac_files = ["a.tf", "b.yaml", "c.bicep", "d.tf.json"]
    non_iac_files = ["e.txt", "f.py"]

    for name in iac_files + non_iac_files:
        p = tmp_path / name
        p.write_text("test", encoding="utf-8")

    collected = collect_iac_files(tmp_path)
    collected_names = {p.name for p in collected}

    for name in iac_files:
        assert is_iac_file(tmp_path / name)
        assert name in collected_names

    for name in non_iac_files:
        assert not is_iac_file(tmp_path / name)
