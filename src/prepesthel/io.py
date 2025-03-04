import os
import sys
import pandas as pd
from pandas import DataFrame
from pathlib import Path
from .participant import Participants
import git
from enum import Enum


class Executors(Enum):
    LOCAL = "Local"
    GITHUB = "Github"


class Results:
    path: Path
    dataFrame: DataFrame

    def __init__(self, path: Path):
        if path.is_file():
            raise IOError(f"File {path} already exists. Aborting.")

        self.path = path
        self.dataFrame = DataFrame()

    def append(self, experiment_summary):
        self.dataFrame = pd.concat([self.dataFrame, DataFrame(experiment_summary, index=[0])], ignore_index=True)

    def output_preliminary(self, silent: bool = False):
        if not silent:
            print(f"Write preliminary output to {self.path}")

        self.dataFrame.to_csv(self.path)

        if not silent:
            print('-' * os.get_terminal_size().columns)
            print(self.dataFrame)
            print('-' * os.get_terminal_size().columns)

    def output_final(
            self,
            participants: Participants,
            args,
            precice_config_params: dict = None,
            silent: bool = False,
            executor: str = Executors.LOCAL.value):
        is_monolithic = len(participants) == 1

        if is_monolithic:  # only a single time step size
            self.dataFrame = self.dataFrame.set_index([f"time step size {p.name}" for p in participants.values()])
        else:  # time window size + len(participants) individual time step sizes
            self.dataFrame = self.dataFrame.set_index(["time window size"] +
                                                      [f"time step size {p.name}" for p in participants.values()])

        if not silent:
            print(f"Write final output to {self.path}")

        git_info = {}
        for participant in participants.values():
            if executor == Executors.LOCAL.value:
                repo = git.Repo(participant.root, search_parent_directories=True)
                chash = str(repo.head.commit)[:7]
                if repo.is_dirty():
                    chash += "-dirty"

                git_info[participant.name] = {
                    "repo": repo.remotes.origin.url,
                    "chash": chash
                }
            elif executor == Executors.GITHUB.value:
                git_info[participant.name] = {
                    "url": os.environ['GITHUB_REPOSITORY'],
                    "repo": os.environ['GITHUB_REF'],
                    "chash": os.environ['GITHUB_SHA']
                }
            else:
                raise Exception(f'''
                    unknown executor {executor}.
                    Please choose one of the following: {[e.value for e in Executors]}
                    ''')

        metadata = {
            "participants version": git_info,
            "participants": participants,
            "run cmd": "python3 " + " ".join(sys.argv),
            "args": args,
        }

        if not is_monolithic:  # coupled simulation
            try:
                import precice
                metadata["precice.get_version_information()"] = precice.get_version_information()
                metadata["precice.__version__"] = precice.__version__
            except ModuleNotFoundError as e:
                import warnings
                warnings.warn(
                    f"Could not import precice. Skipping information in metadata that requires precice. \nModuleNotFoundError: {e}")

            metadata["precice_config_params"] = precice_config_params

        self.path.unlink()

        with open(self.path, 'a') as f:
            for key, value in metadata.items():
                f.write(f"# {key}:{value}\n")
            self.dataFrame.to_csv(f)

        if not silent:
            print('-' * os.get_terminal_size().columns)
            for key, value in metadata.items():
                print(f"{key}:{value}")
            print()
            print(self.dataFrame)
            print('-' * os.get_terminal_size().columns)
