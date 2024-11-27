from .participant import Participants
import datetime
import pandas as pd
from jinja2 import Environment, select_autoescape, FileSystemLoader
from pathlib import Path


def render(template_path, precice_config_params):
    env = Environment(
        loader=FileSystemLoader(Path()),
        autoescape=select_autoescape(['xml'])
    )

    precice_config_template = env.get_template(template_path)

    precice_config_name = Path() / "precice-config.xml"

    with open(precice_config_name, "w") as file:
        file.write(precice_config_template.render(precice_config_params))


def run(participants: Participants, template_path=None, precice_config_params=None):
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


def postproc(participants: Participants, precice_config_params=None):
    print(f"{datetime.datetime.now()}: Postprocessing...")
    summary = {}

    is_monolithic = len(participants) == 1

    if (not is_monolithic) and precice_config_params:
        time_window_size = precice_config_params['time_window_size']
        summary = {"time window size": time_window_size}

    for participant in participants.values():
        df = pd.read_csv(participant.root / f"output-{participant.name}.csv", comment="#")
        if abs(df.times.diff().var() / df.times.diff().mean()) > 10e-10:
            term_size = os.get_terminal_size()
            print('-' * term_size.columns)
            print("WARNING: times vary stronger than expected. Note that adaptive time stepping is not supported.")
            print(df)
            print('-' * term_size.columns)
        summary[f"time step size {participant.name}"] = df.times.diff().mean()

        if is_monolithic:
            summary[f"error Mass-Left {participant.name}"] = df['error Mass-Left'].abs().max()
            summary[f"error Mass-Right {participant.name}"] = df['error Mass-Right'].abs().max()
        else:
            summary[f"error {participant.name}"] = df.errors.abs().max()

    print(f"{datetime.datetime.now()}: Done.")
    return summary
