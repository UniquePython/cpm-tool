from dataclasses import dataclass
from pathlib import Path
from typing import Literal


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

    with manifest_file.open() as file:
        for idx, line in enumerate(file, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split("=", 1)

            # Parse owner/name
            try:
                owner, name = parts[0].split("/", 1)
            except ValueError:
                print(f"Warning: line {idx} : malformed package name. Skipping...")
                continue

            owner = owner.strip()
            name = name.strip()

            # Parse version
            if len(parts) == 2:
                version_str = parts[1].strip()

                if not version_str:
                    print(f"Warning: line {idx} : empty version. Skipping...")
                    continue

                try:
                    version = Version.parse(version_str)
                except ValueError:
                    print(
                        f"Warning: line {idx} : invalid version '{version_str}'. Skipping..."
                    )
                    continue
            else:
                version = "latest"

            packages.append(Package(owner, name, version))

    return packages
