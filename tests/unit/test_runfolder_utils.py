from pathlib import Path

import pytest
import tempfile

from arteria.models.runfolder_utils import list_runfolders, Runfolder, Instrument


@pytest.fixture()
def monitored_directory():
    with tempfile.TemporaryDirectory() as monitored_dir:
        for i in range(3):
            runfolder_path = Path(monitored_dir) / f"runfolder{i}"
            runfolder_path.mkdir()
            (runfolder_path / "CopyComplete.txt").touch()
            if i == 0:
                (runfolder_path / ".arteria").mkdir()
                with open(runfolder_path / ".arteria/state", "w", encoding="utf-8") as state_file:
                    state_file.write("started")
                
                
        (Path(monitored_dir) / "regular_folder").mkdir()

        yield monitored_directory


def test_list_runfolders(monitored_directory):
    runfolders = list_runfolders(monitored_directory)

    assert len(runfolders) == 3
    assert all(
        runfolder.path == f"{monitored_dir}/runfolder{i}"
        for i, runfolder in enumerate(sorted(runfolders, key=lambda r: r.path))
    )


def test_list_runfolders_filtered(monitored_directory):
    runfolder = list_runfolders(monitored_directory, filter_key=lambda r: r.state == "started")

    assert len(runfolder) == 1
    assert runfolder[0].path == f"{monitored_dir}/runfolder0"
    assert runfolder[0].state == "started"


class TestRunfolder():
    def test_get_state(self):
        assert False

    def test_set_state(self):
        assert False

    def get_path(self):
        assert False

    def test_get_metadata(self):
        assert False

class TestInstrument():
    def test_get_marker_file(self):
        assert False