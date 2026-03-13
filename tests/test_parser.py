from pathlib import Path

from cpm.parser import (
    Package,
    Version,
    parse_manifest,
)


def write_manifest(tmp_path, content: str) -> Path:
    manifest_file = tmp_path / "test_manifest.cpm"
    manifest_file.write_text(content)
    return manifest_file


def test_parse_manifest(tmp_path):
    manifest_content = """
# VALID ENTRIES
ananyo/pkg=1.0.0
ananyo/pkg=2.0.0
openai/gpt
torvalds/linux=5.12.3

# MALFORMED OWNER/REPO
-ananyo/pkg=1.0.0
ananyo-/pkg=1.0.0
ananyo//pkg=1.0.0
ananyo/pkg/extra=1.0.0
/pkg=0.0.0
owner/=0.1.0

# MALFORMED VERSIONS
ananyo/pkg=bad.version
bob/lib=
charlie/tool=1.2
dave/repo=1.0.0.0

# COMMENTS AND WHITESPACE
   eve/pkg=0.1.0   
# another comment
frank/lib
    """
    manifest_file = write_manifest(tmp_path, manifest_content)

    packages = parse_manifest(manifest_file)

    # Check valid packages
    expected = [
        Package("ananyo", "pkg", Version(1, 0, 0)),
        Package("openai", "gpt", "latest"),
        Package("torvalds", "linux", Version(5, 12, 3)),
        Package("eve", "pkg", Version(0, 1, 0)),
        Package("frank", "lib", "latest"),
    ]

    assert packages == expected


def test_empty_manifest(tmp_path):
    manifest_file = write_manifest(tmp_path, "")
    packages = parse_manifest(manifest_file)
    assert packages == []


def test_all_invalid(tmp_path):
    manifest_content = """
# all invalid
-ananyo/pkg
alice//pkg
bob/lib=bad.version
"""
    manifest_file = write_manifest(tmp_path, manifest_content)
    packages = parse_manifest(manifest_file)
    assert packages == []


def test_only_latest(tmp_path):
    manifest_content = """
alice/tool
bob/lib
charlie/pkg
"""
    manifest_file = write_manifest(tmp_path, manifest_content)
    packages = parse_manifest(manifest_file)

    expected = [
        Package("alice", "tool", "latest"),
        Package("bob", "lib", "latest"),
        Package("charlie", "pkg", "latest"),
    ]
    assert packages == expected


def test_version_edge_cases(tmp_path):
    manifest_content = """
alice/pkg=0.0.0
bob/lib=999.999.999
"""
    manifest_file = write_manifest(tmp_path, manifest_content)
    packages = parse_manifest(manifest_file)

    expected = [
        Package("alice", "pkg", Version(0, 0, 0)),
        Package("bob", "lib", Version(999, 999, 999)),
    ]
    assert packages == expected
