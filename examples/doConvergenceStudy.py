from jinja2 import Environment, select_autoescape, FileSystemLoader
import pandas as pd
from pathlib import Path
import datetime
import os
import uuid
import argparse
import sys

from pycice_study_tools.participant import Participants, Participant, run
from pycice_study_tools.io import output_preliminary_results, output_final_results


def render(template_path, precice_config_params):
    base_path = Path(__file__).parent.absolute()

    env = Environment(
        loader=FileSystemLoader(base_path),
        autoescape=select_autoescape(['xml'])
    )

    precice_config_template = env.get_template(template_path)

    precice_config_name = base_path / "precice-config.xml"

    with open(precice_config_name, "w") as file:
        file.write(precice_config_template.render(precice_config_params))


def do_experiment(template_path, precice_config_params, participants: Participants):
    if args.template_path:
        render(template_path, precice_config_params)
        print(f"{datetime.datetime.now()}: Start run with parameters {precice_config_params}")
    else:
        print(f"{datetime.datetime.now()}: Start run")

    run(participants)

    print("Postprocessing...")

    if args.template_path:
        time_window_size = precice_config_params['time_window_size']
    summary = {"time window size": time_window_size}

    summary = {}
    for pname, participant in participants.items():
        summary[f"time step size {pname}"] = time_window_size

        t_end = precice_config_params['max_time']
        qoi = "Displacement0"  # quantity of interest

        if pname == "Solid":
            df_ref = pd.read_csv(f"watchpoint_{participant.name}_ref", comment="#", delim_whitespace=True)
            try:
                qoi_ref_at_end = df_ref[df_ref["Time"] == t_end][qoi].to_list()[-1]
            except IndexError:
                qoi_ref_at_end = -1

            df = pd.read_csv(
                participant.root /
                f"precice-{pname}-watchpoint-Flap-Tip.log",
                comment="#",
                delim_whitespace=True)
            qoi_at_end = df[df["Time"] == t_end][qoi].to_list()[-1]
            summary[f"{qoi} {pname}"] = qoi_at_end
            summary[f"error {pname}"] = abs(qoi_at_end - qoi_ref_at_end)
        elif pname == "Fluid":
            pass  # watchpoint is empty for fluid-fake

    print("Done.")

    return summary


def make_parser(n_participants: int):
    n_supported_participants = n_participants

    parser = argparse.ArgumentParser(description="Perform and postprocess multiple runs of preCICE tutorials")
    parser.add_argument(
        "--template",
        help="template for the preCICE configuration file",
        type=str)
    parser.add_argument(
        "-T",
        "--max-time",
        help="Max simulation time",
        type=float,
        default=5.0)
    parser.add_argument(
        "-dt",
        "--base-time-window-size",
        help="Base time window / time step size",
        type=float,
        default=0.001)
    parser.add_argument(
        "-w",
        "--time-window-refinements",
        help="Number of refinements by factor 2 for the time window size",
        type=int,
        default=5)
    parser.add_argument(
        "-tss",
        "--time-stepping-scheme",
        help="Define time stepping scheme used by each solver",
        type=str,
        nargs=n_supported_participants,
        default=n_supported_participants * ["Newmark_beta"])
    parser.add_argument(
        "-o",
        "--out-filename",
        help="Provide a file name. If no file name is provided a UUID will be generated as name. Abort if file already exists.",
        type=str,
    )


if __name__ == "__main__":
    parser = make_parser(n_participants=2)
    args = parser.parse_args()

    df = pd.DataFrame()

    if args.template:
        precice_config_params = {
            'time_window_size': None,  # will be defined later
            'max_time': args.max_time,
        }

    root_folder = Path()

    results_file: Path
    if args.out_filename:  # use file name given by user
        results_file = root_folder / results_file / args.out_filename
    else:  # no file name is given. Create UUID for file name
        results_file = root_folder / results_file / "convergence-studies" / f"{uuid.uuid4()}.csv"

    if results_file.is_file():
        raise IOError(f"File {results_file} already exists. Aborting.")

    watchpoint_folder = results_file.with_suffix('')
    watchpoint_folder.mkdir(parents=False, exist_ok=False)

    participants: Participants = {
        "Fluid": Participant("Fluid", "fluid-fake", ["./run.sh"], [], {}),
        "Solid": Participant("Solid", "solid-fenics", ["./run.sh"], [], {})
    }

    for dt in [args.base_time_window_size * 0.5**i for i in range(args.time_window_refinements)]:
        if args.template:
            precice_config_params['time_window_size'] = dt

        summary = do_experiment(args.template_path, precice_config_params, participants)
        df = pd.concat([df, pd.DataFrame(summary, index=[0])], ignore_index=True)

        # store the watchpoint file
        (participants["Solid"]["root"] /
         "precice-Solid-watchpoint-Flap-Tip.log").rename(watchpoint_folder /
                                                         f"watchpoint_{dt}")

        output_preliminary_results(df, results_file)

    # TODO: Try to use prepesthel.io.output_final_results(df, results_file, participants, args)

    df = df.set_index(['time window size'] + [f'time step size {p.name}' for p in participants.values()])
    print(f"Write final output to {results_file}")

    import git
    import precice

    repo = git.Repo(__file__, search_parent_directories=True)
    chash = str(repo.head.commit)[:7]
    if repo.is_dirty():
        chash += "-dirty"

    metadata = {
        "git repository": repo.remotes.origin.url,
        "git commit": chash,
        "precice.get_version_information()": precice.get_version_information(),
        "precice.__version__": precice.__version__,
        "run cmd": "python3 " + " ".join(sys.argv),
        "args": args,
        "precice_config_params": precice_config_params,
        "participants": participants,
    }

    results_file.unlink()

    with open(results_file, 'a') as f:
        for key, value in metadata.items():
            f.write(f"# {key}:{value}\n")
        df.to_csv(f)

    print('-' * term_size.columns)
    for key, value in metadata.items():
        print(f"{key}:{value}")
    print()
    print(df)
    print('-' * term_size.columns)
