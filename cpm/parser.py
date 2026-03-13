import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# Precompiled regex for GitHub owner/repo validation
PKG_RE = re.compile(
    r"^(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38})/(?P<repo>(?!.*\.git$)[A-Za-z0-9._-]+)$"
)


@dataclass(order=True, frozen=True)
class Version:
    major: int
    minor: int
    patch: int

    def __post_init__(self):
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError(f"Invalid version: {self}")

    @classmethod
    def parse(cls, s: str) -> "Version":
        parts = s.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version string: {s}")
        major, minor, patch = map(int, parts)
        return cls(major, minor, patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass
class Package:
    owner: str
    name: str
    version: Version | Literal["latest"]

    def __str__(self) -> str:
        return f"{self.owner}/{self.name}@{self.version}"


def parse_manifest(manifest_file: Path) -> list[Package]:
    if not manifest_file.exists():
        raise FileNotFoundError(f"{manifest_file} could not be found")
    if not manifest_file.is_file():
        raise IsADirectoryError(f"{manifest_file} is not a file")

    packages: list[Package] = []
    seen = set()  # Track duplicates: (owner, name)

    with manifest_file.open() as file:
        for idx, line in enumerate(file, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("=", 1)
            pkg_id = parts[0].strip()

            match = PKG_RE.match(pkg_id)
            if not match:
                warnings.warn(
                    f"Line {idx}: malformed package name '{pkg_id}'. Skipping...",
                    stacklevel=2,
                )
                continue

            owner = match.group("owner")
            name = match.group("repo")

            if len(parts) == 2:
                version_str = parts[1].strip()
                if not version_str:
                    warnings.warn(
                        f"Line {idx}: empty version. Skipping...", stacklevel=2
                    )
                    continue
                try:
                    version = Version.parse(version_str)
                except ValueError:
                    warnings.warn(
                        f"Line {idx}: invalid version '{version_str}'. Skipping...",
                        stacklevel=2,
                    )
                    continue
            else:
                version = "latest"

            key = (owner, name)
            if key in seen:
                warnings.warn(
                    f"Line {idx}: duplicate package '{owner}/{name}'. Skipping...",
                    stacklevel=2,
                )
                continue
            seen.add(key)

            packages.append(Package(owner, name, version))

    return packages
