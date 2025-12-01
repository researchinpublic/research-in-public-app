#!/bin/bash
# Start mock server from OpenAPI contract using Prism

set -e

OPENAPI_SPEC="${1:-contract/openapi.yaml}"
PORT="${2:-4010}"

# Check if Prism is installed
if ! command -v prism &> /dev/null; then
    echo "Prism not found. Installing..."
    npm install -g @stoplight/prism-cli
fi

# Check if OpenAPI spec exists
if [ ! -f "$OPENAPI_SPEC" ]; then
    echo "Error: OpenAPI spec not found: $OPENAPI_SPEC"
    exit 1
fi

echo "Starting Prism mock server..."
echo "  OpenAPI spec: $OPENAPI_SPEC"
echo "  Port: $PORT"
echo ""
echo "Mock server will be available at: http://localhost:$PORT"
echo "Press Ctrl+C to stop"
echo ""

prism mock "$OPENAPI_SPEC" --port "$PORT" --cors

