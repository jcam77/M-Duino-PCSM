#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT" || exit 1
DEFAULTS_FILE="$REPO_ROOT/config/mduino-defaults.env"

if [ -f "$DEFAULTS_FILE" ]; then
  # shellcheck disable=SC1090
  . "$DEFAULTS_FILE"
fi

MISSING_ITEMS=()
PYTHON_CMD=""
FRONTEND_HOST="${MDUINO_FRONTEND_HOST:-${MDUINO_DEFAULT_FRONTEND_HOST:-127.0.0.1}}"
FRONTEND_PORT="${MDUINO_FRONTEND_PORT:-${MDUINO_DEFAULT_FRONTEND_PORT:-5174}}"
BACKEND_HOST="${MDUINO_BACKEND_HOST:-${MDUINO_DEFAULT_BACKEND_HOST:-127.0.0.1}}"
BACKEND_PORT="${MDUINO_BACKEND_PORT:-${MDUINO_DEFAULT_BACKEND_PORT:-5001}}"

cleanup_sidecar_files() {
  find "$REPO_ROOT" -type f -name '._*' -delete >/dev/null 2>&1 || true
}

prepend_path_if_dir() {
  local candidate="$1"
  [ -d "$candidate" ] || return 0
  case ":$PATH:" in
    *":$candidate:"*) return 0 ;;
  esac
  PATH="$candidate:$PATH"
}

seed_gui_path() {
  prepend_path_if_dir "/opt/homebrew/bin"
  prepend_path_if_dir "/usr/local/bin"
  prepend_path_if_dir "/usr/bin"
  prepend_path_if_dir "/bin"
  prepend_path_if_dir "$HOME/.local/bin"
  prepend_path_if_dir "$HOME/bin"
  prepend_path_if_dir "/snap/bin"
  prepend_path_if_dir "$HOME/.nvm/current/bin"
}

print_header() {
  echo "========================================"
  echo "M-Duino-PCSM Launcher"
  echo "========================================"
}

pause_on_error() {
  if [ -t 0 ]; then
    read -r -p "Press Enter to exit..." _
  fi
}

add_missing() {
  MISSING_ITEMS+=("$1")
}

resolve_python() {
  if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$REPO_ROOT/.venv/bin/python"
    return
  fi
  add_missing "Missing local virtual environment: run Setup-M-Duino-PCSM-LINUX.sh first"
}

check_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    add_missing "Missing tool: $command_name"
  fi
}

check_node_packages() {
  if ! node -e "require('rollup'); require.resolve('vite/package.json'); require.resolve('react/package.json'); require.resolve('react-dom/package.json')" >/dev/null 2>&1; then
    add_missing "Frontend dependencies are incomplete for this machine: run Setup-M-Duino-PCSM-LINUX.sh"
  fi
}

check_python_packages() {
  if [ -z "$PYTHON_CMD" ]; then
    return
  fi
  if ! "$PYTHON_CMD" -c "import flask, serial, mduino_pcsm" >/dev/null 2>&1; then
    add_missing "Python runtime packages are incomplete: run Setup-M-Duino-PCSM-LINUX.sh"
  fi
}

print_missing_summary() {
  echo ""
  echo "M-Duino-PCSM cannot start yet:"
  for item in "${MISSING_ITEMS[@]}"; do
    echo " - $item"
  done
  echo ""
  echo "Recommended fix:"
  echo "  ./Setup-M-Duino-PCSM-LINUX.sh"
  echo ""
}

cleanup() {
  if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1
    wait "$BACKEND_PID" 2>/dev/null
  fi
  if [ -n "${VITE_PID:-}" ] && kill -0 "$VITE_PID" >/dev/null 2>&1; then
    kill "$VITE_PID" >/dev/null 2>&1
    wait "$VITE_PID" 2>/dev/null
  fi
}

http_ok() {
  curl -fsS "$1" >/dev/null 2>&1
}

open_browser() {
  local target_url="$1"
  case "$(uname -s)" in
    Darwin)
      command -v open >/dev/null 2>&1 && open "$target_url" >/dev/null 2>&1 || true
      ;;
    Linux)
      command -v xdg-open >/dev/null 2>&1 && xdg-open "$target_url" >/dev/null 2>&1 || true
      ;;
  esac
}

start_app() {
  local frontend_root_url="http://${FRONTEND_HOST}:${FRONTEND_PORT}"
  local backend_health_url="http://${BACKEND_HOST}:${BACKEND_PORT}/api/health"
  local app_url="${frontend_root_url}/?backendPort=${BACKEND_PORT}"

  if http_ok "$frontend_root_url" && http_ok "$backend_health_url"; then
    echo ""
    echo "M-Duino-PCSM is already running."
    echo "Opening ${app_url}"
    open_browser "$app_url"
    exit 0
  fi

  if http_ok "$backend_health_url"; then
    echo ""
    echo "Reusing existing backend on http://${BACKEND_HOST}:${BACKEND_PORT}"
  else
    echo ""
    echo "Starting backend on http://${BACKEND_HOST}:${BACKEND_PORT} ..."
    MDUINO_BACKEND_DEBUG=1 \
    MDUINO_BACKEND_HOST="$BACKEND_HOST" \
    MDUINO_BACKEND_PORT="$BACKEND_PORT" \
    "$PYTHON_CMD" backend/app.py &
    BACKEND_PID=$!
    trap cleanup EXIT INT TERM

    sleep 2
    if ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
      echo ""
      echo "The backend stopped during startup. Check the error output above."
      pause_on_error
      exit 1
    fi
  fi

  if http_ok "$frontend_root_url"; then
    echo "Frontend already running at ${frontend_root_url}"
    echo "Opening ${app_url}"
    open_browser "$app_url"
    exit 0
  fi

  echo "Starting frontend on ${frontend_root_url} ..."
  echo "App URL:"
  echo "  ${app_url}"

  "$REPO_ROOT/node_modules/.bin/vite" --config frontend/vite.config.js --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --strictPort &
  VITE_PID=$!
  trap cleanup EXIT INT TERM

  if [ "${MDUINO_OPEN_BROWSER:-1}" != "0" ]; then
    (
      for _ in $(seq 1 30); do
        if http_ok "$frontend_root_url"; then
          open_browser "$app_url"
          exit 0
        fi
        sleep 1
      done
    ) &
  fi

  wait "$VITE_PID"
}

print_header
seed_gui_path
cleanup_sidecar_files
check_command node
check_command npm
check_command curl
resolve_python
check_node_packages
check_python_packages

if [ "${#MISSING_ITEMS[@]}" -gt 0 ]; then
  print_missing_summary
  pause_on_error
  exit 1
fi

start_app
