from .participant import Participants
import datetime
import pandas as pd


def run(participants: Participants):
    print(f"{datetime.datetime.now()}: Running ...")

    # start all participants
    for participant in participants.values():
        participant.start()

    # wait until all participants are done
    for participant in participants.values():
        participant.wait()
        
    print(f"{datetime.datetime.now()}: Done.")


def postproc(participants: Participants):
    print(f"{datetime.datetime.now()}: Postprocessing...")
    summary = {}
    for participant in participants.values():
        df = pd.read_csv(participant.root / f"errors-{participant.name}.csv", comment="#")
        if abs(df.times.diff().var() / df.times.diff().mean()) > 10e-10:
            term_size = os.get_terminal_size()
            print('-' * term_size.columns)
            print("WARNING: times vary stronger than expected. Note that adaptive time stepping is not supported.")
            print(df)
            print('-' * term_size.columns)
        summary[f"time step size {participant.name}"] = df.times.diff().mean()
        summary[f"error1 {participant.name}"] = df.errors1.abs().max()
        summary[f"error2 {participant.name}"] = df.errors2.abs().max()
    print(f"{datetime.datetime.now()}: Done.")
    return summary