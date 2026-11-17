import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = str(Path(sys.executable).parent / "eubank-mcp")


def _env(db, tmp_path, role):
    return {
        "PATH": os.environ["PATH"],
        "EUBANK_ROLE": role,
        "EUBANK_OPERATOR_ID": "op-test",
        "EUBANK_DB_PATH": str(db),
        "EUBANK_AUDIT_PATH": str(tmp_path / "audit.jsonl"),
    }


async def _with_session(db, tmp_path, role, fn):
    params = StdioServerParameters(command=SERVER, env=_env(db, tmp_path, role))
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        return await fn(session)


async def _tool_names(session):
    return {t.name for t in (await session.list_tools()).tools}


@pytest.mark.anyio
async def test_attendant_tool_list(seeded_db, tmp_path):
    names = await _with_session(seeded_db, tmp_path, "attendant", _tool_names)
    assert names == {"search_customers", "get_customer_summary"}


@pytest.mark.anyio
async def test_analyst_tool_list(seeded_db, tmp_path):
    names = await _with_session(seeded_db, tmp_path, "analyst", _tool_names)
    assert names == {"search_customers", "get_customer_summary", "get_customer_risk"}


@pytest.mark.anyio
async def test_tools_are_read_only(seeded_db, tmp_path):
    async def annotations(session):
        return [t.annotations for t in (await session.list_tools()).tools]
    for ann in await _with_session(seeded_db, tmp_path, "analyst", annotations):
        assert ann is not None and ann.read_only_hint is True


@pytest.mark.anyio
async def test_call_summary_over_stdio(seeded_db, tmp_path):
    async def call(session):
        return await session.call_tool("get_customer_summary", {"customer_id": "C00004"})
    result = await _with_session(seeded_db, tmp_path, "attendant", call)
    assert not result.is_error
    payload = json.loads(result.content[0].text)
    assert payload["status"] == "ok"
    assert payload["customer"]["name"] == "Lukas Becker"


def test_bad_role_exits(seeded_db, tmp_path):
    env = _env(seeded_db, tmp_path, "admin")
    proc = subprocess.run([SERVER], check=False, env=env, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 2
    assert "EUBANK_ROLE" in proc.stderr


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _schemas(session):
    return {t.name: (t.input_schema, t.output_schema) for t in (await session.list_tools()).tools}


@pytest.mark.anyio
async def test_every_tool_publishes_output_schema(seeded_db, tmp_path):
    schemas = await _with_session(seeded_db, tmp_path, "analyst", _schemas)
    for name, (_, output) in schemas.items():
        assert output is not None, name


@pytest.mark.anyio
async def test_attendant_summary_schema_hides_analyst_fields(seeded_db, tmp_path):
    schemas = await _with_session(seeded_db, tmp_path, "attendant", _schemas)
    text = json.dumps(schemas["get_customer_summary"][1])
    assert "nif_masked" in text
    for field in ("age", "country", "is_pep", "credit_score"):
        assert f'"{field}"' not in text


@pytest.mark.anyio
async def test_analyst_schemas_expose_their_fields(seeded_db, tmp_path):
    schemas = await _with_session(seeded_db, tmp_path, "analyst", _schemas)
    assert '"age"' in json.dumps(schemas["get_customer_summary"][1])
    assert '"is_pep"' in json.dumps(schemas["get_customer_risk"][1])


@pytest.mark.anyio
async def test_input_schemas_describe_limits(seeded_db, tmp_path):
    schemas = await _with_session(seeded_db, tmp_path, "attendant", _schemas)
    query = schemas["search_customers"][0]["properties"]["query"]
    assert "100" in query["description"] and "NIF" in query["description"]
    assert "C00004" in schemas["get_customer_summary"][0]["properties"]["customer_id"]["description"]
