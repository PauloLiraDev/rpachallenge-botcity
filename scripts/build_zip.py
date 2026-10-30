"""Gera dist/rpachallenge.zip com o que o Runner precisa (sem .env, testes ou venv)."""

import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "rpachallenge.zip"
INCLUDE = ("bot.py", "requirements.txt", "src", "resources")
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache"}


def export_requirements() -> None:
    """requirements.txt é o que o Runner lê: sempre regenerado do uv.lock, sem dev."""
    output = subprocess.run(
        [
            "uv",
            "export",
            "--no-dev",
            "--no-hashes",
            "--no-emit-project",
            "--format",
            "requirements-txt",
            "--python",
            "3.11",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    (ROOT / "requirements.txt").write_text(output, encoding="utf-8")


def files_to_pack() -> list[Path]:
    files: list[Path] = []
    for name in INCLUDE:
        path = ROOT / name
        candidates = [path] if path.is_file() else sorted(path.rglob("*")) if path.is_dir() else []
        files += [f for f in candidates if f.is_file() and not EXCLUDED_PARTS & set(f.parts)]
    return files


def main() -> int:
    export_requirements()
    DIST.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(DIST, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in files_to_pack():
            archive.write(file, file.relative_to(ROOT).as_posix())
    print(f"{DIST.relative_to(ROOT)} ({DIST.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
