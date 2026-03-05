#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/manus-lite-chat/app}"
VENV_DIR="${VENV_DIR:-/opt/manus-lite-chat/venv}"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"

if ! command -v dnf >/dev/null 2>&1; then
  echo "This script expects an OpenCloudOS/RHEL-like system with dnf"
  exit 1
fi

sudo dnf install -y ${PYTHON_BIN} ${PYTHON_BIN}-devel gcc

mkdir -p "${APP_ROOT}"
mkdir -p "$(dirname "${VENV_DIR}")"

if [ ! -d "${VENV_DIR}" ]; then
  ${PYTHON_BIN} -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip setuptools wheel

cd "${APP_ROOT}"
pip install -e .

mkdir -p data logs

cat <<MSG
Bootstrap complete.
- App root: ${APP_ROOT}
- Venv: ${VENV_DIR}
Next:
1) cp .env.prod.example .env
2) Edit .env with your provider keys/endpoints
3) Start app with: ${VENV_DIR}/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
MSG
