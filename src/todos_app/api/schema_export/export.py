from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from todos_app.api.schema_export.registry import (
	PUBLIC_API_SCHEMAS,
	SchemaExportMode,
)


@dataclass(frozen=True, slots=True)
class SchemaExportResult:
	output_dir: Path
	index_path: Path
	bundle_path: Path
	model_paths: dict[str, Path]


def _schema_filename(name: str) -> str:
	return f"{name}.schema.json"


def export_model_schema(model: type[BaseModel], *, mode: SchemaExportMode) -> dict[str, Any]:
	return model.model_json_schema(mode=mode)


def build_bundle_schema(*, mode: SchemaExportMode) -> dict[str, Any]:
	bundle_defs: dict[str, Any] = {}

	for entry in PUBLIC_API_SCHEMAS:
		schema = export_model_schema(entry.model, mode=mode)
		nested_defs = schema.pop("$defs", {})
		bundle_defs.update(nested_defs)
		bundle_defs[entry.name] = schema

	return {
		"$schema": "https://json-schema.org/draft/2020-12/schema",
		"title": "Todos API models",
		"description": "JSON Schemas for public HTTP request and response bodies.",
		"$defs": bundle_defs,
	}


def build_index_payload(
	*,
	mode: SchemaExportMode,
	model_paths: Mapping[str, str],
) -> dict[str, Any]:
	return {
		"$schema": "https://json-schema.org/draft/2020-12/schema",
		"title": "Todos API model index",
		"description": "Manifest of exported Pydantic API schemas for client code generation.",
		"mode": mode,
		"models": [
			{
				"name": entry.name,
				"group": entry.group,
				"description": entry.description,
				"file": model_paths[entry.name],
			}
			for entry in PUBLIC_API_SCHEMAS
		],
	}


def export_public_schemas(
	output_dir: Path,
	*,
	mode: SchemaExportMode = "validation",
) -> SchemaExportResult:
	output_dir.mkdir(parents=True, exist_ok=True)

	model_paths: dict[str, Path] = {}
	relative_model_paths: dict[str, str] = {}

	for entry in PUBLIC_API_SCHEMAS:
		filename = _schema_filename(entry.name)
		path = output_dir / filename
		schema = export_model_schema(entry.model, mode=mode)
		_write_json(path, schema)
		model_paths[entry.name] = path
		relative_model_paths[entry.name] = filename

	index_path = output_dir / "index.json"
	_write_json(
		index_path,
		build_index_payload(mode=mode, model_paths=relative_model_paths),
	)

	bundle_path = output_dir / "bundle.schema.json"
	_write_json(bundle_path, build_bundle_schema(mode=mode))

	return SchemaExportResult(
		output_dir=output_dir,
		index_path=index_path,
		bundle_path=bundle_path,
		model_paths=model_paths,
	)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
	with path.open("w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2, ensure_ascii=False)
		handle.write("\n")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Export public API Pydantic models as JSON Schema files.",
	)
	parser.add_argument(
		"output_dir",
		nargs="?",
		default="schemas/json",
		help="Directory for exported schema files (default: schemas/json).",
	)
	parser.add_argument(
		"--mode",
		choices=("validation", "serialization"),
		default="validation",
		help="Pydantic JSON Schema mode (default: validation).",
	)
	return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
	args = _parse_args(argv)
	result = export_public_schemas(Path(args.output_dir), mode=args.mode)
	print(f"Wrote {len(result.model_paths)} model schemas to {result.output_dir}")
	print(f"Index: {result.index_path}")
	print(f"Bundle: {result.bundle_path}")


if __name__ == "__main__":
	main()
