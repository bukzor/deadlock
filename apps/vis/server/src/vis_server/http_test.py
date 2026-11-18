from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from .http import app
from .types import BadRequest, JsonObj, Params, Query


def _echo(given: Params) -> Sequence[JsonObj]:
    return [{"z": 1.5, "a": [None, True], "given": dict(given)}, {"text": "naïve"}]


def _refuse(given: Params) -> Sequence[JsonObj]:
    raise BadRequest(f"no: {given.get('why', '?')}")


def _crash(_: Params) -> Sequence[JsonObj]:
    raise RuntimeError("a bug")


FAKE: Mapping[str, Query] = {
    "echo": Query({"x": "anything (optional)", "y": "anything (optional)"}, _echo),
    "refuse": Query({"why": "the reason"}, _refuse),
    "crash": Query({}, _crash),
}
ECHO_XY = '{"a":[null,true],"given":{"x":"1","y":"two words"},"z":1.5}\n{"text":"na\\u00efve"}\n'


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(app(FAKE, client=tmp_path / "absent"))


class DescribeApi:
    def it_lists_the_queries_one_line_each(self, client: TestClient):
        response = client.get("/api")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/jsonl"
        assert response.text == (
            '{"params":{"x":"anything (optional)","y":"anything (optional)"},"query":"echo"}\n'
            '{"params":{"why":"the reason"},"query":"refuse"}\n'
            '{"params":{},"query":"crash"}\n'
        )

    def it_answers_a_query_as_compact_sorted_jsonl(self, client: TestClient):
        response = client.get("/api/echo", params={"x": "1", "y": "two words"})
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/jsonl"
        assert response.text == ECHO_XY

    def it_answers_a_bad_request_with_400_and_one_error_line(self, client: TestClient):
        response = client.get("/api/refuse?why=because")
        assert (response.status_code, response.headers["content-type"]) == (400, "application/jsonl")
        assert response.text == '{"error":"no: because"}\n'

    def it_answers_an_unknown_query_with_404_and_one_error_line(self, client: TestClient):
        response = client.get("/api/nope")
        assert (response.status_code, response.headers["content-type"]) == (404, "application/jsonl")
        assert response.text == '{"error":"unknown query: nope (accepted: echo, refuse, crash)"}\n'

    def it_rejects_a_repeated_parameter(self, client: TestClient):
        response = client.get("/api/echo?x=1&x=2")
        assert (response.status_code, response.text) == (400, '{"error":"repeated parameter: x"}\n')

    def it_lets_a_bug_fail_loudly(self, client: TestClient):
        with pytest.raises(RuntimeError, match="a bug"):
            _ = client.get("/api/crash")
        quiet = TestClient(app(FAKE, client=Path("/nonexistent")), raise_server_exceptions=False)
        assert quiet.get("/api/crash").status_code == 500


class DescribeClient:
    def it_serves_the_built_client_at_the_root(self, tmp_path: Path):
        _ = (tmp_path / "index.html").write_text("<p>vis</p>")
        client = TestClient(app(FAKE, client=tmp_path))
        assert (client.get("/").status_code, client.get("/").text) == (200, "<p>vis</p>")
        assert client.get("/api/echo").status_code == 200

    def it_serves_nothing_at_the_root_without_a_build(self, client: TestClient):
        assert client.get("/").status_code == 404
        assert client.get("/api").status_code == 200

