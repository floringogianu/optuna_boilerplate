# Optuna boilerplate

Takes a `base.yaml` containing your experiment's settings and `tune.yaml`
containing the `optuna` search space.
From these two it creates candidate experiment configurations that it can run in
parallel, on multiple machines that share the same volume.

For example on one machine you can run:

```shell
nohup python search.py configs/tune_init results/2024Aug27_hp_tune  --max_trials 100 > tune.log &
nohup python search.py configs/tune_init results/2024Aug27_hp_tune  --max_trials 100 > tune.log &
nohup python search.py configs/tune_init results/2024Aug27_hp_tune  --max_trials 100 > tune.log &
nohup python search.py configs/tune_init results/2024Aug27_hp_tune  --max_trials 100 > tune.log &
```

to launch 4 workers followed by the same commands on another machine for a total
of 8 workers in parallel.

The total number of trials across all workers is `100`.

## dependencies:

```shell
mamba/conda/pip install optuna optuna-dashboard
```

## check results

Launch the [optuna dashboard](https://optuna-dashboard.readthedocs.io/en/stable/getting-started.html):

```shell
optuna-dashboard sqlite:///results/2024Aug27_hp_tune/optuna.db
```