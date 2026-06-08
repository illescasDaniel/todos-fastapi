#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIAGRAM_DIR="$ROOT/docs/diagram"
OUT_DIR="$ROOT/docs/images"

mkdir -p "$OUT_DIR"

export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:+$JAVA_TOOL_OPTIONS }-Djava.awt.headless=true"

PLANTUML_ARGS=(-Playout=smetana -tsvg -o "$OUT_DIR")

render() {
	if command -v plantuml >/dev/null 2>&1; then
		plantuml "${PLANTUML_ARGS[@]}" "$DIAGRAM_DIR"/*.puml
	elif [[ -f "$ROOT/tools/plantuml.jar" ]]; then
		java -Djava.awt.headless=true -jar "$ROOT/tools/plantuml.jar" "${PLANTUML_ARGS[@]}" "$DIAGRAM_DIR"/*.puml
	else
		echo "PlantUML not found. Install: pacman -S plantuml graphviz" >&2
		echo "Or download plantuml.jar to tools/plantuml.jar (see docs/architecture.md)." >&2
		exit 1
	fi
}

render

echo "Wrote SVG diagrams to $OUT_DIR"
