# doConvergenceStudy
A python-based workflow for parameter studies of preCICE tutorial cases

## How to use:

* Script automatically generates a `precice-config.xml` from a `precice-config-template.xml` (see `examples`).
* Copy `src/doConvergenceStudy.py` and `examples/precice-config-template.xml` to the tutorial case (currently only supports `tutorials/prependicular-flap`)
* Run `python3 ./doConvergenceStudy.py precice-config-template.xml`. Use `python3 ./doConvergenceStudy.py --help` to learn about additional parameters.
* The script `doConvergenceStudy.py` defines how the error is measured. Make sure to provide a file that is named `watchpoint_{participant['case']}_ref`, if you want to get an error estimate.

**Important:** The interface is currently experimental and work-in-progress.
