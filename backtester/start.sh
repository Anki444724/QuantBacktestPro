#!/usr/bin/env bash
# Start the QuantBacktest Pro application
# Usage: ./start.sh

set -e

cd "$(dirname "$0")"
exec python3 start.py "$@"
