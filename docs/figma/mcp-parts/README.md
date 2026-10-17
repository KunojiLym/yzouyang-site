# Figma MCP export parts

Verbatim JSON from the Figma MCP variable/text-style export (no `web` bindings).  
`scripts/finalize_figma_mcp_snapshot.py` merges these with the existing snapshot’s `web` fields and writes `docs/figma/variables.json`.

Refresh when Figma changes:

1. Overwrite these four files with **verbatim** Figma MCP export JSON (no `web` fields).
2. `uv run python scripts/finalize_figma_mcp_snapshot.py`
3. `uv run python scripts/test_design_system_sync.py`

`scripts/export_mcp_parts_from_snapshot.py` only strips `web` from an already-verified `variables.json` to refresh the parts tree; it does not call Figma.
