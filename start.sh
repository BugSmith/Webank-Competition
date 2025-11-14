#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$REPO_ROOT/.venv"
FRONTEND_DIR="$REPO_ROOT/Fin-ai"
DEFAULT_PIPELINE_INPUT="$REPO_ROOT/tests/fixtures/pipeline/sample_payload.json"

ensure_venv() {
  if [[ ! -d "$VENV_PATH" ]]; then
    python3 -m venv "$VENV_PATH"
  fi
}

activate_venv() {
  # shellcheck disable=SC1090
  source "$VENV_PATH/bin/activate"
}

install_python_deps() {
  ensure_venv
  activate_venv
  pip install --upgrade pip
  pip install -r "$REPO_ROOT/requirements.txt"
  pip install -r "$FRONTEND_DIR/requirements.txt"
}

install_frontend_deps() {
  npm install --prefix "$FRONTEND_DIR"
}

cmd_install() {
  install_python_deps
  install_frontend_deps
  echo "[start.sh] 所有依赖安装完成。"
}

cmd_pipeline() {
  local input="${1:-$DEFAULT_PIPELINE_INPUT}"
  local user_id="${2:-UTSZ}"
  local output="${3:-/tmp/utsz_insights.json}"
  ensure_venv
  activate_venv
  export AGNO_MODEL_ID="${AGNO_MODEL_ID:-qwen-turbo-latest}"
  export DASHSCOPE_BASE_URL="${DASHSCOPE_BASE_URL:-https://dashscope.aliyuncs.com/compatible-mode/v1}"
  python -m agents.cli refresh-insights \
    --input "$input" \
    --user-id "$user_id" \
    --output "$output"
}

cmd_backend() {
  ensure_venv
  activate_venv
#   export PYTHONPATH="$REPO_ROOT:$PYTHONPATH"
  export FLASK_ENV="${FLASK_ENV:-development}"
  python "$FRONTEND_DIR/app.py"
}

cmd_frontend() {
  install_frontend_deps
  npm run dev --prefix "$FRONTEND_DIR"
}

cmd_all() {
  echo "[start.sh] 请在不同终端分别运行："
  echo "1) $0 backend"
  echo "2) $0 frontend"
  echo "3) $0 pipeline (可选，用于刷新洞察)"
}

usage() {
  cat <<'EOF'
用法:
  ./start.sh install          # 安装 Python 与前端依赖
  ./start.sh pipeline [input user_id output]
  ./start.sh backend          # 启动 Flask 后端
  ./start.sh frontend         # 启动 Vite 前端
  ./start.sh all              # 打印多终端运行建议
EOF
}

main() {
  local cmd="${1:-help}"
  shift || true
  case "$cmd" in
    install)  cmd_install "$@";;
    pipeline) cmd_pipeline "$@";;
    backend)  cmd_backend "$@";;
    frontend) cmd_frontend "$@";;
    all)      cmd_all;;
    *)        usage;;
  esac
}

main "$@"
