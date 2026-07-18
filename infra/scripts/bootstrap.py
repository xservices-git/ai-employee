"""Bootstrap script: setup dev environment."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> None:
    """Run command, raise on failure."""
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"Failed: {cmd}", file=sys.stderr)
        sys.exit(1)


def check_uv() -> None:
    """Check uv is installed."""
    if shutil.which("uv") is None:
        print("ERROR: 'uv' not found. Install: https://docs.astral.sh/uv/getting-started/installation/", file=sys.stderr)
        sys.exit(1)


def check_ollama() -> bool:
    """Check if Ollama is installed."""
    return shutil.which("ollama") is not None


def main() -> None:
    """Bootstrap the dev environment."""
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print("=== AI Employee V3.0 Bootstrap ===\n")

    # 1. Check uv
    print("1. Checking uv...")
    check_uv()

    # 2. Install Python deps
    print("\n2. Installing Python dependencies...")
    run(["uv", "sync", "--all-extras"])

    # 3. Create data dir
    print("\n3. Creating data directory...")
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "chroma").mkdir(exist_ok=True)
    (data_dir / "logs").mkdir(exist_ok=True)

    # 4. Copy .env
    print("\n4. Setting up .env...")
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"Created {env_file}")
    else:
        print(f"{env_file} already exists")

    # 5. Check Ollama
    print("\n5. Checking Ollama...")
    if check_ollama():
        print("Ollama found. To pull models, run:")
        print("  ollama pull qwen2.5:4b")
        print("  ollama pull llama3.1:8b")
        print("  ollama pull nomic-embed-text:v1.5")
    else:
        print("WARNING: Ollama not found. Install from https://ollama.com/download")
        print("  Or run: docker compose -f infra/docker-compose.yaml up -d ollama")

    # 6. Install web deps
    print("\n6. Installing web dependencies...")
    web_dir = project_root / "web"
    if (web_dir / "package.json").exists():
        run(["npm", "install"], cwd=web_dir)

    # 7. Run tests
    print("\n7. Running tests...")
    run(["uv", "run", "pytest", "tests/unit", "-v"])

    print("\n=== Bootstrap complete! ===")
    print("\nNext steps:")
    print("  make serve-api   # Terminal 1: API on :8000")
    print("  make serve-web   # Terminal 2: Web on :3000")
    print("  make eval        # Run eval suite")


if __name__ == "__main__":
    main()
