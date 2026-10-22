"""Bounded regression checks for MAC output line wrapping."""
import builtins
import copy
import importlib
from io import StringIO

import pytest

from mac_inp.Read_XYPlot import Read_XYPlot
from mac_out import mac_out


class BoundedOutput(StringIO):
    """Stop a broken writer before it can fill memory with continuations."""

    def __init__(self):
        super().__init__()
        self.writes = 0

    def write(self, text):
        self.writes += 1
        if self.writes > 100:
            raise AssertionError("Line wrapping exceeded 100 writes")
        return super().write(text)


def render(text, cutoff=75, delimiter=","):
    writer = mac_out.__new__(mac_out)
    writer.str_cutoff = cutoff
    writer.file = BoundedOutput()
    writer._write_str(text, delim=delimiter)
    return writer.file.getvalue()


@pytest.mark.parametrize("cutoff", [1, 8, 75])
@pytest.mark.parametrize("text", ["X" * 200, "NAME=" + "A" * 150,
                                  "α" * 100],
                         ids=["plain", "keyword", "unicode"])
def test_unbreakable_token_is_written_intact(text, cutoff):
    assert render(text, cutoff) == text


@pytest.mark.parametrize("prefix,cutoff,delimiter", [
    (" MODE=1 ", 20, ","),
    ("ABC,", 3, ","),
    ("MODE=1;", 6, ";"),
])
def test_long_tail_after_successful_split(prefix, cutoff, delimiter):
    token = "NAME=" + "X" * 150 + "\n"
    assert render(prefix + token, cutoff, delimiter) == prefix + "&\n " + token


@pytest.mark.parametrize("text,cutoff,delimiter,expected", [
    ("", 75, ",", ""),
    ("X" * 75, 75, ",", "X" * 75),
    ("abc def", 20, ",", "abc def"),
    (" " + "X" * 100, 20, ",", " " + "X" * 100),
    ("abc,def", 3, ",", "abc,&\n def"),
    ("ab cd ef", 3, ",", "ab &\n cd &\n ef"),
    ("abc;def", 3, ";", "abc;&\n def"),
    ("abc,def", 10, ",", "abc,def"),
    ("a," + "X" * 100, 20, ",", "a," + "X" * 100),
])
def test_existing_wrapping_output_is_unchanged(
        text, cutoff, delimiter, expected):
    assert render(text, cutoff, delimiter) == expected


def test_output_errors_are_not_swallowed():
    expected = OSError("output is unavailable")

    class FailingOutput:
        def write(self, text):
            raise expected

    writer = mac_out.__new__(mac_out)
    writer.str_cutoff = 75
    writer.file = FailingOutput()
    with pytest.raises(OSError) as caught:
        writer._write_str("NAME=" + "A" * 100)
    assert caught.value is expected


class BoundedFile:
    """Use a real file while bounding writes during baseline regressions."""

    def __init__(self, target):
        self.target = target
        self.writes = 0

    def __enter__(self):
        self.target.__enter__()
        return self

    def __exit__(self, *args):
        return self.target.__exit__(*args)

    def write(self, text):
        self.writes += 1
        if self.writes > 100:
            raise AssertionError("MAC output did not finish within 100 writes")
        return self.target.write(text)


@pytest.mark.parametrize("cutoff", [20, 75])
@pytest.mark.parametrize("name", ["A" * 100, "stress_" + "x" * 150,
                                  "α" * 100],
                         ids=["plain", "prefixed", "unicode"])
def test_long_plot_name_round_trips_through_public_writer(
        tmp_path, monkeypatch, name, cutoff):
    module = importlib.import_module("mac_out.mac_out")
    real_open = builtins.open

    def bounded_open(*args, **kwargs):
        return BoundedFile(real_open(*args, **kwargs))

    monkeypatch.setattr(module, "open", bounded_open, raising=False)
    plots = {
        "freq": 1,
        "macro": {"macro": 1, "results": {
            "0": {"name": name, "x": 2, "y": 8}}},
        "micro": {"micro": 0, "results": {}},
    }
    keywords = {"xy": copy.deepcopy(plots)}
    filename = tmp_path / "plot.MAC"
    mac_out(keywords, name=str(filename), str_cutoff=cutoff)
    assert keywords == {"xy": plots}
    assert filename.read_text(encoding="utf-8").endswith("*END")
    with filename.open(encoding="utf-8") as source:
        assert source.readline() == "*XYPLOT\n"
        assert Read_XYPlot(source) == plots
        assert source.readline() == "*END"


def test_short_deck_output_is_unchanged(tmp_path):
    filename = tmp_path / "short.MAC"
    mac_out({"title": "Example", "print": {"npl": 1},
             "probtype": {"mech": 1, "vect": 0}}, name=str(filename))
    assert filename.read_text(encoding="utf-8") == (
        "Example\n*PRINT\n npl=1\n*PROBLEM_TYPE\n mech=1 vect=0\n*END")
