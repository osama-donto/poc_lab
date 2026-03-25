"""Data model schemas for interactive mapping."""

import typing

import attrs


@attrs.define(frozen=True)
class CanonicalField:
    """Definition of a canonical field for a role."""

    field_id: str  # e.g., "vetcove_item_id"
    field_type: str  # string | number | bool | object | list
    required: bool
    description: str | None = None


@attrs.define(frozen=True)
class ParseConfig:
    """Configuration for parsing structured files (xlsx, json)."""

    sheet_names: tuple[str, ...] | None = (
        None  # xlsx sheets to try (first match wins, else active sheet)
    )
    header_row: int = 1  # 1-indexed row containing headers
    min_data_row: int = 2  # 1-indexed first data row
    root_key: str | None = (
        None  # JSON path to extract (e.g., "items" for {"items": [...]})
    )


@attrs.define(frozen=True)
class DerivedFrom:
    """Specifies that a role can be derived from another role's field.

    When a role with derives_from is unassigned but its parent role is assigned,
    the role is considered satisfied (derived from parent at runtime).
    """

    parent_role_id: str  # Role to derive from (e.g., "aliases_references")
    path: str  # Field path to extract (e.g., "unit_of_measure")


@attrs.define
class RoleMetadata:
    """Metadata defining expectations for a file role."""

    role_id: str  # e.g., "products", "cubex_catalog"
    expected_format: str  # csv | json | xlsx
    expected_shape: str  # list-of-objects | object | tabular
    canonical_fields: list[CanonicalField]
    header_aliases: dict[str, list[str]]  # canonical -> [known raw aliases]
    description: str
    parse_config: ParseConfig | None = None
    expected_row_range: tuple[int, int] | None = None
    role_priority: int = 1  # lower = higher priority (1=primary, 2=secondary, etc.)
    is_shape_only: bool = False  # True if classification is based on format/shape only
    required: bool = (
        True  # False for optional roles (missing produces warnings, not errors)
    )
    derives_from: DerivedFrom | None = (
        None  # If set, role can be derived from parent role's field
    )


@attrs.define
class ObservedMetadata:
    """Metadata extracted from parsing an uploaded file."""

    file: str
    detected_format: str  # csv | json | xlsx | unknown
    parse_success: bool
    parse_errors: list[str]  # fatal errors that prevent successful parsing
    parse_warnings: list[str] = attrs.Factory(
        list,
    )  # non-fatal warnings (e.g., mixed-type arrays)
    shape: str | None = None  # list-of-objects | object | tabular | None
    headers: list[str] | None = None  # csv/xlsx headers or derived from JSON list items
    top_level_keys: list[str] | None = None  # for JSON object roles (capped at 100)
    row_count: int | None = None  # for tabular/list-of-objects
    sample_rows: list[dict[str, typing.Any]] | None = None  # up to 10 sample rows/items
    key_coverage: dict[str, float] | None = (
        None  # for JSON list-of-objects: key -> coverage %
    )
    # For JSON objects: store raw data to enable root_key extraction in second pass
    raw_json_data: dict[str, typing.Any] | None = None
    # For XLSX: store source path to enable re-parsing with role's parse_config
    source_path: str | None = None


@attrs.define
class ClassificationResult:
    """Result of classifying a file to a role."""

    file: str
    assigned_role: str | None
    confidence: float
    missing_required: list[str]  # canonical field ids not matched
    extra_headers: list[str]  # raw headers/keys not mapped to any canonical field
    field_map: dict[str, str]  # raw header -> canonical field id
    assignment_reason: str  # auto | suggested | unassigned
    warnings: list[str] = attrs.Factory(list)
    # Variant tracking for Phase 2 adapter
    matched_format: str | None = None  # "csv" | "json" | None
    matched_shape: str | None = None  # "tabular" | "list-of-objects" | "object" | None
    matched_parse_config: ParseConfig | None = None  # Includes root_key if applicable
    # Header normalization for XLSX: raw header -> expected header (JSONata-compatible)
    header_normalization_map: dict[str, str] = attrs.Factory(dict)


@attrs.define(frozen=True)
class UnassignedFile:
    """Information about a file that could not be assigned to a role."""

    file: str
    best_match_role: str | None
    best_match_score: float
    reason: str  # score_below_threshold | no_matching_format | parse_failed


@attrs.define
class ClassificationOutput:
    """Complete output of the classification process."""

    profile_id: str
    observed_metadata: list[ObservedMetadata]
    classification_results: list[ClassificationResult]
    unassigned_files: list[UnassignedFile]
    unassigned_roles: list[str]
    warnings: list[
        str
    ]  # profile-level warnings (unassigned roles, competing files, etc.)
