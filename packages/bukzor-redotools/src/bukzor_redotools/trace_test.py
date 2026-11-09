import json
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeGuard, cast

import pytest

from .trace import Span, build_tree, latest_root, main, to_trace


def _log(*lines: str) -> str:
    return "".join(f"{line}\n" for line in lines)


def _names(span: Span) -> list[str]:
    return [span.target, *(n for kid in span.children for n in _names(kid))]


def _spans(events: Sequence[Mapping[str, object]]) -> dict[str, Mapping[str, object]]:
    return {str(e["name"]): e for e in events if e["ph"] == "X"}


# `all` builds sub/a, which builds ../c (so c, at the top), then fails x
LOGS = {
    "all": _log(
        "@@REDO:do:1:100.0000@@ sub/a",
        "@@REDO:done:1:104.0000@@ 0 sub/a",
        "@@REDO:do:1:104.5000@@ x",
        "@@REDO:done:1:105.0000@@ 2 x",
        "@@REDO:unchanged:1:106.0000@@ y",
    ),
    "sub/a": _log(
        "some stderr chatter",
        "@@REDO:do:2:101.0000@@ ../c",
        "@@REDO:done:2:103.0000@@ 0 ../c",
    ),
}


class DescribeBuildTree:
    def it_resolves_children_against_their_parents_directory(self):
        tree = build_tree("all", LOGS)
        assert _names(tree) == ["all", "sub/a", "c", "x"]

    def it_records_each_childs_span_and_exit_code(self):
        a, x = build_tree("all", LOGS).children
        assert (a.start, a.end, a.rv) == (100.0, 104.0, 0)
        assert (x.start, x.end, x.rv) == (104.5, 105.0, 2)

    def it_spans_the_root_from_its_first_to_its_last_log_line(self):
        tree = build_tree("all", LOGS)
        assert (tree.start, tree.end, tree.rv) == (100.0, 106.0, None)

    def it_ignores_a_childs_log_from_a_later_build(self):
        """sub/a rebuilt on its own afterward: that log isn't this build's."""
        logs = {**LOGS, "sub/a": _log("@@REDO:do:3:200.0000@@ ../c", "@@REDO:done:3:201.0000@@ 0 ../c")}
        assert _names(build_tree("all", logs)) == ["all", "sub/a", "x"]

    def it_runs_an_unfinished_child_to_its_last_known_moment(self):
        """A build still running, or interrupted: `do` without `done`."""
        a = build_tree("all", RUNNING).children[0]
        assert (a.target, a.start, a.end, a.rv) == ("sub/a", 100.0, 101.0, None)


# a build still running: sub/a has started ../c, and nothing has finished
RUNNING = {
    "all": _log("@@REDO:do:1:100.0000@@ sub/a"),
    "sub/a": _log("@@REDO:do:2:101.0000@@ ../c"),
}


class DescribeLatestRoot:
    def it_picks_the_build_that_finished_last(self):
        logs = {**LOGS, "old": _log("@@REDO:do:1:50.0000@@ z", "@@REDO:done:1:51.0000@@ 0 z")}
        assert latest_root(logs) == "all"

    def it_skips_logs_that_a_parents_span_accounts_for(self):
        """Deeper logs end later while a build runs; they're still not roots."""
        assert latest_root(RUNNING) == "all"

    def it_treats_a_child_rebuilt_on_its_own_as_a_root(self):
        logs = {**LOGS, "sub/a": _log("@@REDO:do:3:200.0000@@ ../c", "@@REDO:done:3:201.0000@@ 0 ../c")}
        assert latest_root(logs) == "sub/a"


class DescribeToTrace:
    def it_emits_microseconds_from_the_build_start(self):
        events = _spans(to_trace(build_tree("all", LOGS)))
        assert (events["c"]["ts"], events["c"]["dur"]) == (1_000_000, 2_000_000)

    def it_keeps_nested_spans_on_one_lane(self):
        events = _spans(to_trace(build_tree("all", LOGS)))
        assert {e["tid"] for e in events.values()} == {0}

    def it_moves_overlapping_siblings_to_separate_lanes(self):
        """A parallel (-j) build: siblings overlap, so they can't share a lane."""
        logs = {
            "all": _log(
                "@@REDO:do:1:0.0000@@ p",
                "@@REDO:do:1:1.0000@@ q",
                "@@REDO:done:1:3.0000@@ 0 p",
                "@@REDO:done:1:4.0000@@ 0 q",
            )
        }
        lanes = {name: e["tid"] for name, e in _spans(to_trace(build_tree("all", logs))).items()}
        assert lanes["p"] != lanes["q"], lanes

    def it_colors_a_failed_target(self):
        events = _spans(to_trace(build_tree("all", LOGS)))
        assert events["x"].get("cname") == "terrible"
        assert "cname" not in events["sub/a"]


def _is_str_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping)


def _is_sequence(value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(value, list)


def _events_of(text: str) -> list[Mapping[str, object]]:
    trace = cast(object, json.loads(text))  # json is untyped; the guards below narrow it
    assert _is_str_mapping(trace), trace
    events = trace["traceEvents"]
    assert _is_sequence(events), events
    return [e for e in events if _is_str_mapping(e)]


_DO = {
    "all.do": "redo-ifchange sub/a\n",
    "sub/a.do": "redo-ifchange ../c\n",
    "c.do": "echo c\n",
}


@pytest.mark.skipif(not shutil.which("redo"), reason="redo not installed")
class DescribeMain:
    def it_traces_a_real_build(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
        (tmp_path / "sub").mkdir()
        for name, body in _DO.items():
            _ = (tmp_path / name).write_text(body)
        _ = subprocess.run(["redo", "all"], cwd=tmp_path, check=True, capture_output=True)

        monkeypatch.chdir(tmp_path / "sub")  # finds .redo by walking up
        main(["redo-trace"])
        events = _events_of(capsys.readouterr().out)
        assert sorted(_spans(events)) == ["all", "c", "sub/a"]
