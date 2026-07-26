"""The phyl CLI writes the file it is asked to, for each layout."""

import pytest

from phylustrator.cli import main


def test_cli_saves_svg(tmp_path):
    nwk = tmp_path / "t.nwk"
    nwk.write_text("((A:1,B:1)C:1,D:2)R;")
    out = tmp_path / "fig.svg"
    assert main([str(nwk), "-o", str(out)]) == 0
    assert out.exists() and out.read_text().lstrip().startswith("<")


@pytest.mark.parametrize("flag", ["--radial", "--unrooted"])
def test_cli_layout_shortcuts(tmp_path, flag):
    nwk = tmp_path / "t.nwk"
    nwk.write_text("((A:1,B:1)C:1,D:2)R;")
    out = tmp_path / "fig.svg"
    assert main([str(nwk), flag, "--no-labels", "-o", str(out)]) == 0
    assert out.exists()


def test_cli_missing_file_errors(tmp_path):
    with pytest.raises(SystemExit):
        main([str(tmp_path / "nope.nwk"), "-o", str(tmp_path / "x.svg")])
