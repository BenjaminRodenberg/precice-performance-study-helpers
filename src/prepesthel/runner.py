from .participant import Participants
import datetime
import pandas as pd
from jinja2 import Environment, select_autoescape, FileSystemLoader
from pathlib import Path
import os
import numpy as np
import warnings


def render(template_path: Path,
           precice_config_params: dict):
    env = Environment(
        loader=FileSystemLoader(Path()),
        autoescape=select_autoescape(['xml'])
    )

    precice_config_template = env.get_template(template_path)

    precice_config_name = Path() / "precice-config.xml"

    with open(precice_config_name, "w") as file:
        file.write(precice_config_template.render(precice_config_params))


def run(participants: Participants,
        template_path: Path = None,
        precice_config_params: dict = None):

    if template_path and precice_config_params:
        render(template_path, precice_config_params)

    print(f"{datetime.datetime.now()}: Running ...")

    # start all participants
    for participant in participants.values():
        participant.start()

    # wait until all participants are done
    for participant in participants.values():
        participant.wait()

    print(f"{datetime.datetime.now()}: Done.")


def postproc(participants: Participants,
             precice_config_params: dict = None,
             tolerance: float = 10e-10,
             silent: bool = False):
    print(f"{datetime.datetime.now()}: Postprocessing...")
    summary = {}

    is_monolithic = len(participants) == 1

    if (not is_monolithic) and precice_config_params:
        time_window_size = precice_config_params['time_window_size']
        summary = {"time window size": time_window_size}

    for participant in participants.values():
        df = pd.read_csv(participant.root / f"output-{participant.name}.csv", comment="#")
        dts = df.times.diff()  # get time step sizes from data
        coefficient_of_variation = np.sqrt(dts.var()) / dts.mean()
        if abs(coefficient_of_variation) > tolerance:  # if time step sizes vary a lot raise a warning
            if not silent:
                term_size = os.get_terminal_size()
                print('-' * term_size.columns)
                warnings.warn(f'''
                Times vary stronger than expected.
                Coefficient of variations {coefficient_of_variation} is larger than provided tolerance of {tolerance}.
                Note that adaptive time stepping is not supported. The maximum dt will be used in the output.
                ''')
                print(df)
                print('-' * term_size.columns)
            summary[f"time step size {participant.name}"] = dts.max()
        else:
            summary[f"time step size {participant.name}"] = dts.mean()

        if is_monolithic:
            summary[f"error Mass-Left {participant.name}"] = df['error Mass-Left'].abs().max()
            summary[f"error Mass-Right {participant.name}"] = df['error Mass-Right'].abs().max()
        else:
            summary[f"error {participant.name}"] = df.errors.abs().max()

    print(f"{datetime.datetime.now()}: Done.")
    return summary
