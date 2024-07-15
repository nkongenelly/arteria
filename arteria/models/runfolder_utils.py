from pathlib import Path
import logging
import os
import time
import re
import xmltodict

from arteria.models.state import State


log = logging.getLogger(__name__)
def list_runfolders(path, filter_key=lambda r: True):
    return []


class Runfolder():
    def __init__(self, path, grace_minutes=0):
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
        except StopIteration:
            raise AssertionError("File [Rr]unParameters.xml not found in runfolder {path}")

        marker_file = Instrument(self.run_parameters).completed_marker_file
        assert (
            marker_file.exists()
            and time.time() - os.path.getmtime(marker_file) > grace_minutes * 60
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
    def __init__(self, run_parameters):
        self.run_parameters = run_parameters
        self.runparameter_instrument_id_keys = [
            "InstrumentName", "InstrumentId", "ScannerID",
            "InstrumentSerialNumber"
        ]

    @property
    def completed_marker_file(self):
        if self.run_parameters:
            instrument, instrument_keys = self.get_instrument()
            completed_marker_file = instrument_keys.get("completed_marker_file")
            return completed_marker_file


    def get_instrument(self):
        instrument_id = self.get_instrument_id()
        instrument_marker_dict = self.get_instrument_marker_dict()
        return next(
            (
                (instrument, instrument_keys)
                for instrument, instrument_keys in instrument_marker_dict.items()
                if re.search(instrument_keys.get('id_pattern'), instrument_id)
            ),
            (
                None, {'completed_marker_file': 'RTAComplete.txt'}
            )
        )


    def get_instrument_id(self):
        instrument_id = self.run_parameters.get('Setup', {}).get('ScannerID')
        if instrument_id is None:
            instrument_id = next(
                self.run_parameters.get(key)
                for key in self.runparameter_instrument_id_keys
                if key in self.run_parameters.keys()
            )
        return instrument_id

    def get_instrument_marker_dict(self):
        return {
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


