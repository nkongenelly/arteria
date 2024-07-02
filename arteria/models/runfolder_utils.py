from pathlib import Path

from arteria.models.state import State


def list_runfolders(path, filter_key=lambda r: True):
    return []

class Runfolder:
    def __init__(self, path):
        self.path = Path(path)
        assert self.path.is_dir()
        assert (
            (self.path / "CopyComplete.txt").exists()
            or (self.path / "RTAComplete.txt").exists()
        )
        (self.path / ".arteria").mkdir(exist_ok=True)
        self._state_file = (self.path / ".arteria/state")
        if not self._state_file.exists():
            self._state_file.write_text("ready")

    @property
    def state(self):
        return State(self._state_file.read_text().strip())

    @state.setter
    def state(self, new_state):
        assert new_state in State
        self._state_file.write_text(new_state.value)


    @property
    def metadata(self):
        pass

class Instrument:
    def __init__(self, run_params_file):
        pass
