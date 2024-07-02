from pathlib import Path
import tempfile

import pytest

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


@pytest.fixture()
def runfolder():
    with tempfile.TemporaryDirectory(suffix="RUNFOLDER") as runfolder_path:
        runfolder_path = Path(runfolder_path)
        (runfolder_path / "CopyComplete.txt").touch()
        (runfolder_path / ".arteria").mkdir()
        with open(runfolder_path / ".arteria/state", "w", encoding="utf-8") as state_file:
            state_file.write("started")

        yield Runfolder(runfolder_path)


def test_list_runfolders(monitored_directory):
    runfolders = list_runfolders(monitored_directory)

    assert len(runfolders) == 3
    assert all(
        runfolder.path == f"{monitored_directory}/runfolder{i}"
        for i, runfolder in enumerate(sorted(runfolders, key=lambda r: r.path))
    )


def test_list_runfolders_filtered(monitored_directory):
    runfolder = list_runfolders(
        monitored_directory,
        filter_key=lambda r: r.state == "started"
    )

    assert len(runfolder) == 1
    assert runfolder[0].path == f"{monitored_directory}/runfolder0"
    assert runfolder[0].state == "started"


class TestRunfolder():
    def test_get_state(self, runfolder):
        assert runfolder.state == "started"

    def test_set_state(self, runfolder):
        runfolder.state = "done"
        assert runfolder.state == "done"

    def get_path(self, runfolder):
        assert runfolder.path.endswith("RUNFOLDER")

    def test_get_metadata(self):
        assert False

class TestInstrument():
    def test_get_marker_file(self):
        assert False
