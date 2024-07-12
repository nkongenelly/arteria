import os
import re
import time
import logging
import xmltodict

from pathlib import Path
from arteria.models.state import State
from arteria.models.config import Config

log = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "completed_marker_grace_minutes": 0,
}


def list_runfolders(monitored_directories, filter_key=lambda r: True):
    """
    Returns list of Runfolders in the monitored_directories
    according to the state filter provided (filter_key), or all
    runfolders when no state filter is given.
    """
    runfolders = []
    for monitored_directory in monitored_directories:
        monitored_dir_path = Path(monitored_directory)
        for subdir in monitored_dir_path.iterdir():
            try:
                if filter_key(runfolder := Runfolder(monitored_dir_path / subdir)):
                    runfolders.append(runfolder)
            except AssertionError as e:
                if e == f"File [Rr]unParameters.xml not found in runfolder {subdir}":
                    continue

    return runfolders

class Runfolder():
    """
    A class to manipulate runfolders on disk
    """
    def __init__(self, path):
        self.config = Config(DEFAULT_CONFIG)
        self.path = Path(path)
        assert self.path.is_dir()
        try:
            run_parameter_file = next(
                path
                for path in [
                    self.path / "RunParameters.xml",
                    self.path / "runParameters.xml",
                ]
                if path.exists()
            )
            self.run_parameters = xmltodict.parse(run_parameter_file.read_text())["RunParameters"]
        except StopIteration as exc:
            raise AssertionError(f"File [Rr]unParameters.xml not found in runfolder {path}") from exc

        marker_file_name = Instrument(self.run_parameters).completed_marker_file
        marker_file = (self.path / marker_file_name)
        assert (
            marker_file.exists()
            and (
                time.time() - os.path.getmtime(marker_file)
                > self.config["completed_marker_grace_minutes"] * 60
            )
        )

        (self.path / ".arteria").mkdir(exist_ok=True)
        self._state_file = (self.path / ".arteria/state")
        if not self._state_file.exists():
            self._state_file.write_text("ready")

    @property
    def state(self):
        return State(self._state_file.read_text().strip().lower())

    @state.setter
    def state(self, new_state):
        assert new_state in State
        self._state_file.write_text(new_state.value)

    @property
    def metadata(self):
        """
        Extract metadata from the runparameter file

        Returns
        -------
            metadata: a dict containing up to two keys: "reagent_kit_barcode"
            and "library_tube_barcode"
        """
        if not self.run_parameters:
            log.warning(f"No metadata found for runfolder {self.path}")

        metadata = {}

        try:
            metadata["reagent_kit_barcode"] = \
                self.run_parameters["ReagentKitBarcode"]
        except KeyError:
            log.debug("Reagent kit barcode not found")

        try:
            metadata["library_tube_barcode"] = \
                self.run_parameters["RfidsInfo"]["LibraryTubeSerialBarcode"]
        except KeyError:
            try:
                metadata["library_tube_barcode"] = \
                    next(
                        consumable["SerialNumber"]
                        for consumable in self.run_parameters["ConsumableInfo"]["ConsumableInfo"]
                        if consumable["Type"] == "SampleTube"
                    )
            except (KeyError, StopIteration):
                log.debug("Library tube barcode not found")

        return metadata


class Instrument:
    RUNPARAMETERS_INSTRUMENT_ID_KEYS = [
        "InstrumentName", "InstrumentId", "ScannerID",
        "InstrumentSerialNumber"
    ]

    INSTRUMENT_MARKER_DICT = {
        "NovaSeq": {
            'id_pattern': '^A', 'completed_marker_file': 'CopyComplete.txt'
        },
        "NovaSeqXPlus": {
            'id_pattern': '^LH', 'completed_marker_file': 'CopyComplete.txt'
        },
        "ISeq": {
            'id_pattern': '^FS', 'completed_marker_file': 'CopyComplete.txt'
        },
        "MiSeq": {
            'id_pattern': '^M', 'completed_marker_file': 'RTAComplete.txt'
        },
        "HiSeq": {
            'id_pattern': '^D', 'completed_marker_file': 'RTAComplete.txt'
        },
        "HiSeqX": {
            'id_pattern': '^ST-E', 'completed_marker_file': 'RTAComplete.txt'
        }
    }

    def __init__(self, run_parameters):
        self.run_parameters = run_parameters
        assert self.run_parameters

    @property
    def completed_marker_file(self):
        """
        Returns the completed_marker_file name(str) which is specific to the instrument
        """
        instrument, instrument_keys = self.instrument
        completed_marker_file = instrument_keys["completed_marker_file"]
        return completed_marker_file

    @property
    def instrument(self):
        """
        Returns a dictionary of the instrument id_pattern and completed_marker file
        These details are currently hardcoded in the INSTRUMENT_MARKER_DICT variable
        """
        return next(
            (
                (instrument, instrument_keys)
                for instrument, instrument_keys in self.INSTRUMENT_MARKER_DICT.items()
                if re.search(instrument_keys.get('id_pattern'), self.instrument_id)
            ),
            (
                None, {'completed_marker_file': 'RTAComplete.txt'}
            )
        )

    @property
    def instrument_id(self):
        """
        Returns the id of the instrument used.
        """
        instrument_id = self.run_parameters.get('Setup', {}).get('ScannerID')
        if instrument_id is None:
            try:
                instrument_id = next(
                    self.run_parameters.get(key)
                    for key in self.RUNPARAMETERS_INSTRUMENT_ID_KEYS
                    if key in self.run_parameters.keys()
                )
            except StopIteration as e:
                raise TypeError(f"{self.instrument} is not recognized") from e
        return instrument_id
