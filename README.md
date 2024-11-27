# preCICE performance study helpers

A python-based workflow for parameter studies of preCICE tutorial cases

The package `prepesthel` provides utilities for parameter studies of coupled simulations using multiple executables. This includes

* `prepesthel.participants` for definition one or multiple `Participant`s that contribute to a coupled simulation. This includes parameters needed for the individual runs etc.
* `prepesthel.runner` for orchestration of the participants according to their definition and postprocessing of the results. The `prepesthel.runner` also provides functionality to automatically creates a `precice-config.xml` from a given template. Refer to `examples/precice-config-template.xml`
* `prepesthel.io` for outputting reports of multiple runs including metadata about the runs.

## Installation

Run `pip3 install .` in this folder. Or install the latest release from PyPI via `pip3 install prepesthel`.

## How to use

`examples/doConvergenceStudy.py` shows an example script using `prepesthel` for a convergence study of a coupled simulation.
