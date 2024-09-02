# Optuna boilerplate

Takes a `base.yaml` containing your experiment's settings and `tune.yaml`
containing the `optuna` search space.
From these two it creates candidate experiment configurations that it can run in
parallel, on multiple machines that share the same volume.

For example on one machine you can run:

```shell
nohup python search.py configs/tune_init --max_trials 100 > tune.log &
nohup python search.py configs/tune_init --max_trials 100 > tune.log &
nohup python search.py configs/tune_init --max_trials 100 > tune.log &
nohup python search.py configs/tune_init --max_trials 100 > tune.log &
```

to launch 4 workers followed by the same commands on another machine for a total
of 8 workers in parallel.

The `optuna.db` and the artefacts of each run will be stored under the default `./results`.

The total number of trials across all workers is `100`.

### alternate study path

Optuna stores multiple studies in the same database.
Having multiple studies each with hundreds of trials can slow-down the `sqlite3` database and make experiment management and organization difficult.
Therefore you can further group multiple studies together with the `--results-dir` option:

```shell
nohup python search.py configs/A_study --results-dir ./results/study_optimizers --max_trials 100 > tune.log &
nohup python search.py configs/B_study --results-dir ./results/study_optimizers --max_trials 100 > tune.log &
```

will create an `optuna.db` file in `./results/study_optimizers` containing two different studies.

## dependencies:

```shell
mamba/conda/pip install optuna optuna-dashboard
```

## check results

Launch the [optuna dashboard](https://optuna-dashboard.readthedocs.io/en/stable/getting-started.html):

```shell
optuna-dashboard sqlite:///results/2024Aug27_hp_tune/optuna.db
```