import json
from typing import cast
from pathlib import Path

import pytest
import typed_json
from starlette.applications import Starlette
from starlette.testclient import TestClient

from .__main__ import main
from .http import app
from .http_test import ECHO_XY, FAKE


def query(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(["query", *argv], FAKE)
    out, err = capsys.readouterr()
    return code, out, err


class DescribeQuery:
    def it_prints_the_lines_to_stdout(self, capsys: pytest.CaptureFixture[str]):
        assert query(capsys, "echo", "x=1", "y=two words") == (0, ECHO_XY, "")

    def it_prints_one_compact_json_object_per_line_for_jq(self, capsys: pytest.CaptureFixture[str]):
        _, out, _ = query(capsys, "echo", "x=1")
        lines = out.splitlines(keepends=True)
        assert len(lines) == 2, out
        for line in lines:
            assert line.endswith("\n") and line.count("\n") == 1, line
            parsed = typed_json.loads(line)
            assert isinstance(parsed, dict), parsed
            assert json.dumps(parsed, separators=(",", ":"), sort_keys=True) + "\n" == line

    def it_prints_the_same_bytes_as_http(self, capsys: pytest.CaptureFixture[str], tmp_path: Path):
        http = TestClient(app(FAKE, client=tmp_path))
        for argv, url in [
            (["echo", "x=1", "y=two words"], "/api/echo?x=1&y=two+words"),
            (["echo"], "/api/echo"),
        ]:
            code, out, _ = query(capsys, *argv)
            response = http.get(url)
            assert (code, out.encode()) == (0, response.content), argv

    def it_splits_each_argument_at_its_first_equals_sign(self, capsys: pytest.CaptureFixture[str]):
        _, out, _ = query(capsys, "echo", "x=a=b", "y=")
        assert '"given":{"x":"a=b","y":""}' in out

    class WhenTheRequestIsBad:
        def it_prints_the_error_line_to_stderr_and_exits_2(self, capsys: pytest.CaptureFixture[str]):
            assert query(capsys, "refuse", "why=because") == (2, "", '{"error":"no: because"}\n')

        def it_treats_an_unknown_query_alike(self, capsys: pytest.CaptureFixture[str]):
            expected = '{"error":"unknown query: nope (accepted: echo, refuse, crash)"}\n'
            assert query(capsys, "nope") == (2, "", expected)

        def it_treats_a_repeated_parameter_alike(self, capsys: pytest.CaptureFixture[str]):
            assert query(capsys, "echo", "x=1", "x=2") == (2, "", '{"error":"repeated parameter: x"}\n')

        def it_rejects_an_argument_without_an_equals_sign_as_a_usage_error(self, capsys: pytest.CaptureFixture[str]):
            with pytest.raises(SystemExit) as exit:
                _ = main(["query", "echo", "x"], FAKE)
            assert exit.value.code == 2
            assert "expected k=v, got 'x'" in capsys.readouterr().err


class DescribeServe:
    def it_runs_uvicorn_on_the_registry(self, monkeypatch: pytest.MonkeyPatch):
        calls: list[tuple[object, str, int]] = []

        def run(asgi: object, *, host: str, port: int) -> None:
            calls.append((asgi, host, port))

        monkeypatch.setattr("uvicorn.run", run)
        assert main(["serve"], FAKE) == 0
        assert main(["serve", "--host", "0.0.0.0", "--port", "9000"], FAKE) == 0
        assert [(host, port) for _, host, port in calls] == [("127.0.0.1", 8787), ("0.0.0.0", 9000)]
        served = calls[0][0]
        assert isinstance(served, Starlette), served
        assert TestClient(served).get("/api").text.startswith('{"params":{"x":')

    def it_reloads_on_the_sources_when_asked(self, monkeypatch: pytest.MonkeyPatch):
        calls: list[tuple[object, dict[str, object]]] = []

        def run(asgi: object, **kwargs: object) -> None:
            calls.append((asgi, kwargs))

        monkeypatch.setattr("uvicorn.run", run)
        assert main(["serve", "--reload", "--port", "9000"], FAKE) == 0
        asgi, kwargs = calls[0]
        assert asgi == "vis_server.http:live"
        assert (kwargs["factory"], kwargs["reload"], kwargs["port"]) == (True, True, 9000)
        watched = kwargs["reload_dirs"]
        assert isinstance(watched, list)
        assert [Path(str(d)).name for d in cast("list[object]", watched)] == ["vis_server", "bukzor_deadlock", "bukzor_deadlock_damage", "bukzor_deadlock_lookup"]
