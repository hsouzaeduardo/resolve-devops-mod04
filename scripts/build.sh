#!/usr/bin/env bash
# Monta o site para um ambiente específico, substituindo os placeholders do HTML.
# Uso: ./scripts/build.sh <env-key> "<Nome do Ambiente>" <dir-saida>
#   env-key: dev | homolog | prod
set -euo pipefail

ENV_KEY="${1:?informe env-key (dev|homolog|prod)}"
ENV_NAME="${2:?informe o nome do ambiente}"
OUT_DIR="${3:-dist}"

VERSION="${VERSION:-$(git describe --tags --always 2>/dev/null || echo v0.0.0)}"
COMMIT="${COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo local)}"
RUN_NUMBER="${GITHUB_RUN_NUMBER:-0}"
DEPLOY_TIME="$(date -u '+%Y-%m-%d %H:%M UTC')"

echo "» build: env=${ENV_KEY} version=${VERSION} commit=${COMMIT} -> ${OUT_DIR}"

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"
cp -r src/* "${OUT_DIR}/"

# Substitui placeholders apenas no index.html
sed -i \
  -e "s/__ENV_KEY__/${ENV_KEY}/g" \
  -e "s/__ENV_NAME__/${ENV_NAME}/g" \
  -e "s/__VERSION__/${VERSION}/g" \
  -e "s/__COMMIT__/${COMMIT}/g" \
  -e "s/__RUN_NUMBER__/${RUN_NUMBER}/g" \
  -e "s|__DEPLOY_TIME__|${DEPLOY_TIME}|g" \
  "${OUT_DIR}/index.html"

echo "» ok"
