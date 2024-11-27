from pathlib import Path
from typing import List, Dict, Optional
from subprocess import Popen


class ParticipantName(str):
    pass


class Participant():
    name: ParticipantName  # name of the Participant
    root: Path             # root path to run participant from
    exec: List[str]        # how to execute the participant, e.g. python3 script.py
    params: List[str]      # list of positional arguments that will be used. Results in python3 script.py param1 ...
    # dict with keyword arguments that will be used. Results in python3 script.py param1 ... k1=v1 k2=v2 ...
    kwargs: Dict[str, str | None]
    logfile: Optional[Path]  # logfile of this participant
    proc: Optional[Popen]  # handle for subprocess running this participant

    def __init__(self, name: str, root: Path, exec: List[str], params: List[str], kwargs: Dict[str, str | None]):
        self.name = name
        self.root = root
        self.exec = exec
        self.params = params
        self.kwargs = kwargs

    def start(self):
        self.logfile = self.root / f"stdout-{self.name}.log"
        with open(self.logfile, "w") as outfile:
            cmd = self.exec + self.params + \
                [f"{keyword}={value}" for keyword, value in self.kwargs.items()]
            self.proc = Popen(cmd, cwd=self.root, stdout=outfile)

    def wait(self):
        self.proc.wait()
        if self.proc.returncode != 0:
            raise Exception(f'Experiment failed for participant {self.name}. See logfile {self.logfile}')


class Participants(Dict[ParticipantName, Participant]):
    pass
