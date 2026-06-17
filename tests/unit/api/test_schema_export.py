import json
from pathlib import Path

import pytest

from todos_app.api.schema_export.export import (
	build_bundle_schema,
	build_index_payload,
	export_model_schema,
	export_public_schemas,
)
from todos_app.api.schema_export.registry import PUBLIC_API_SCHEMAS
from todos_app.api.todos.schemas import TodoCreate


pytestmark = pytest.mark.unit


def test_given_todo_create_when_exporting_model_schema_then_includes_title_and_properties() -> None:
	# given

	# when
	schema = export_model_schema(TodoCreate, mode="validation")

	# then
	assert schema["title"] == "TodoCreate"
	assert "title" in schema["properties"]
	assert schema["properties"]["title"]["type"] == "string"


def test_given_public_schemas_when_building_bundle_then_contains_all_models() -> None:
	# given

	# when
	bundle = build_bundle_schema(mode="validation")

	# then
	assert bundle["title"] == "Todos API models"
	assert "$defs" in bundle
	for entry in PUBLIC_API_SCHEMAS:
		assert entry.name in bundle["$defs"]


def test_given_public_schemas_when_building_index_then_lists_every_model() -> None:
	# given
	model_paths = {entry.name: f"{entry.name}.schema.json" for entry in PUBLIC_API_SCHEMAS}

	# when
	index = build_index_payload(mode="validation", model_paths=model_paths)

	# then
	assert index["mode"] == "validation"
	assert len(index["models"]) == len(PUBLIC_API_SCHEMAS)
	assert index["models"][0]["name"] == PUBLIC_API_SCHEMAS[0].name


def test_given_output_dir_when_exporting_public_schemas_then_writes_files(tmp_path: Path) -> None:
	# given
	output_dir = tmp_path / "schemas"

	# when
	result = export_public_schemas(output_dir, mode="validation")

	# then
	assert result.index_path.is_file()
	assert result.bundle_path.is_file()
	assert len(result.model_paths) == len(PUBLIC_API_SCHEMAS)

	for entry in PUBLIC_API_SCHEMAS:
		path = result.model_paths[entry.name]
		assert path.is_file()
		payload = json.loads(path.read_text(encoding="utf-8"))
		assert payload["title"] == entry.name

	bundle = json.loads(result.bundle_path.read_text(encoding="utf-8"))
	assert "TodoResponse" in bundle["$defs"]
	assert "TodoCreate" in bundle["$defs"]
