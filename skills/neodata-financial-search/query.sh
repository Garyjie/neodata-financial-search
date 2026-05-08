#!/usr/bin/env bash
# NeoData 金融数据查询 - Shell 封装
#
# Usage:
#   bash query.sh "腾讯最新财报"
#   bash query.sh "贵州茅台股价"
#   bash query.sh "上证指数"
#
# 环境变量:
#   NEODATA_TIMEOUT - 超时时间(秒) (默认: 15)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${1:-}" ]]; then
    echo "用法: bash query.sh <query>"
    echo "示例:"
    echo "  bash query.sh \"贵州茅台股价\""
    echo "  bash query.sh \"上证指数\""
    echo "  bash query.sh \"比亚迪\""
    exit 1
fi

QUERY="$1"
TIMEOUT="${NEODATA_TIMEOUT:-15}"

# 调用 Python 脚本
python3 "${SCRIPT_DIR}/query.py" --query "${QUERY}" --timeout "${TIMEOUT}"
