from argparse import ArgumentParser, Namespace
from functools import partial
from pathlib import Path
from typing import Callable

import optuna

from options import Opt


def run(opt: Opt, cb: Callable[[int, dict], None]) -> None:
    """Function containing your training code.

    `opt` contains all the settings and hyperparameters required for configuring
    your model, optimizers, data-loading, etc.
    """
    for epoch in range(opt.epoch_num):
        
        # model.train()
        # metrics = model.validate()

        # a dictionary with the validation accuracy and/or
        # other metrics you might care to optimize.
        metrics: dict[str, float]

        cb(epoch, metrics)


def runner(
    trial: optuna.Trial,
    base_hp: Opt,
    tune_hp: Opt,
    metric_name: str = "acc",
) -> float:
    """The function called by `optuna.optimize`.
    For flexibility
    """
    opt = suggest_config(trial, base_hp, tune_hp)
    # set paths and save config
    opt.out_dir.mkdir(exist_ok=True, parents=True)
    opt.to_yaml(opt.out_dir / "cfg.yaml")

    def report_and_prune(step: int, metrics: dict) -> None:
        trial.set_user_attr("last_score", metrics[metric_name])
        trial.report(metrics[metric_name], step)
        if trial.should_prune():
            raise optuna.TrialPruned()

    run(opt, cb=report_and_prune)
    return trial.user_attrs["last_score"]


def suggest_config(trial: optuna.Trial, base_hp: Opt, tune_hp: Opt) -> Opt:
    """Takes a base config and a search space, querries optuna for trial
    hyperparameters and returns a full trial config.
    """
    flat_base: dict = base_hp.to_flat_dict()
    flat_tune: dict = tune_hp.to_flat_dict()
    candidate: dict = {}
    for k, v in flat_tune.items():
        kind, args = v
        if kind == "int":
            low, high, step, log = args
            candidate[k] = trial.suggest_int(k, low, high, step=step, log=log)
        elif kind == "float":
            low, high, step, log = args
            candidate[k] = trial.suggest_float(k, low, high, step=step, log=log)
        elif kind == "categorical":
            candidate[k] = trial.suggest_categorical(k, args)
        else:
            raise ValueError(f"trial.suggest not implemented for kind `{kind}`.")
    print(candidate)
    trial_opt = Opt.from_flat_dict(Opt._recursive_update(flat_base, candidate))
    print(trial_opt)
    trial_opt.out_dir = trial_opt.out_dir / f"trial_{trial.number:04d}"
    return trial_opt


def main(opt: Namespace) -> None:
    base_hp = Opt.from_yaml(Path(opt.config_root) / "base.yaml")
    tune_hp = Opt.from_yaml(Path(opt.config_root) / "tune.yaml")

    # make the trial aware of the output directory
    base_hp.out_dir = Path(opt.result_root)
    base_hp.out_dir.mkdir(exist_ok=True)

    # create the objective
    objective = partial(runner, base_hp=base_hp, tune_hp=tune_hp, metric_name="acc")

    study = optuna.create_study(
        study_name="second_search",
        storage=f"sqlite:///{opt.result_root}/optuna.db",
        pruner=optuna.pruners.SuccessiveHalvingPruner(
            min_resource=5,
            reduction_factor=4,
        ),
        direction="maximize",
        load_if_exists=True,
    )

    study.optimize(
        objective,
        callbacks=[
            optuna.study.MaxTrialsCallback(
                opt.max_trials,
                states=None,
                # states=(optuna.trial.TrialState.COMPLETE,)
            )
        ],
    )


if __name__ == "__main__":
    parser = ArgumentParser("TuneRL")
    parser.add_argument("config_root", type=str)
    parser.add_argument("result_root", type=str)
    parser.add_argument("--max_trials", dest="max_trials", type=int)
    main(parser.parse_args())