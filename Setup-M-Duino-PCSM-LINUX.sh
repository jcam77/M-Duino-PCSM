#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

cleanup_sidecar_files() {
  find . -type f -name '._*' -delete 2>/dev/null || true
}

hash_project_path() {
  if command -v shasum >/dev/null 2>&1; then
    printf '%s' "$REPO_ROOT" | shasum | awk '{print $1}'
  elif command -v sha1sum >/dev/null 2>&1; then
    printf '%s' "$REPO_ROOT" | sha1sum | awk '{print $1}'
  else
    REPO_ROOT="$REPO_ROOT" python3 - <<'PY'
import hashlib
import os
print(hashlib.sha1(os.environ["REPO_ROOT"].encode("utf-8")).hexdigest())
PY
  fi
}

ensure_venv_link() {
  local venv_root
  local venv_hash
  local venv_target
  local backup_name

  case "$(uname -s)" in
    Darwin)
      venv_root="/private/tmp/mduino-pcsm-venvs"
      ;;
    Linux)
      venv_root="/tmp/mduino-pcsm-venvs"
      ;;
    *)
      venv_root="$REPO_ROOT/.venv-store"
      ;;
  esac

  venv_hash="$(hash_project_path)"
  venv_target="$venv_root/$venv_hash"
  REAL_VENV_PATH="$venv_target"

  mkdir -p "$venv_root"

  if [ -e ".venv" ] && [ ! -L ".venv" ]; then
    backup_name=".venv.broken-$(date +%Y%m%d-%H%M%S)"
    mv .venv "$backup_name"
    echo "Moved broken local .venv to $backup_name"
  fi

  if [ -L ".venv" ] && [ ! -e ".venv" ]; then
    rm -f .venv
  fi

  if [ ! -L ".venv" ]; then
    ln -s "$venv_target" .venv
  fi

  if [ ! -f "$venv_target/bin/activate" ]; then
    rm -rf "$venv_target"
    echo "Creating virtual environment at $venv_target..."
    python3 -m venv "$venv_target"
  fi

  if [ ! -f "$venv_target/bin/activate" ]; then
    echo "Virtual environment was not created correctly at $venv_target"
    exit 1
  fi
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required but was not found in PATH."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but was not found in PATH."
  exit 1
fi

cleanup_sidecar_files
ensure_venv_link

source "$REAL_VENV_PATH/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install --no-build-isolation -e .
python -m pip install -r backend/requirements.txt
npm install

echo
echo "M-Duino-PCSM setup completed."
echo "Virtual environment: $REPO_ROOT/.venv"
echo "Real environment path: $(cd .venv && pwd)"
echo "Next step:"
echo "  ./Run-M-Duino-PCSM-LINUX.sh"
