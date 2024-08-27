from argparse import Namespace
from pathlib import Path
from typing import Any, Self

import yaml


# TODO: separate a FlatDict class.
class Opt(Namespace):
    """[L]iftoff[O]ptions is a Namespace with support for:
    - loading and saving `yaml`
    - convert to and from `dict` and flat `dict`
    - very pretty printing
    - a special convention where fields ending in `_`, eg.: `message_`, are
    preserved as is, usually dicts.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @staticmethod
    def from_dict(d: dict) -> "Opt":
        """Recursive conversion of a dict in a LiftOpt.
        Both `a` and `a_` keys are added tot the Namespace:
            - `a` to to facilitate argument passing like `f(**opt.field)`.
            - `a_` is required to allow casting to dict and flat dict.
        """
        lopt = Opt()
        for key, value in d.items():
            name = key.rstrip("_")
            if isinstance(value, dict) and not key.endswith("_"):
                setattr(lopt, name, Opt.from_dict(value))
            else:
                setattr(lopt, name, value)
                setattr(lopt, key, value)
        return lopt

    def to_dict(self, d=None) -> dict:
        """Recursive conversion from LiftoffOptions/Namespace to dict.
        Key `a` is evicted if `a_` exists.
        """
        d = self if d is None else d
        dct: dict = {}
        for key, value in d.__dict__.items():
            skey = key.rstrip("_")
            if skey in dct:
                dct.pop(skey)
            if isinstance(value, Namespace):
                dct[key] = self.to_dict(value)
            else:
                dct[key] = value
        return dct

    def from_flat_dict(flat_dict: dict) -> "Opt":
        """Expand {a: va, b.c: vbc, b.d: vbd} to {a: va, b: {c: vbc, d: vbd}}.

        Opposite of `flatten_dict`.

        If not clear from above we want:
            {'lr':             0.0011,
            'gamma':           0.95,
            'dnd.size':        2000,
            'dnd.lr':          0.77,
            'dnd.sched.end':   0.0,
            'dnd.sched.steps': 1000}
        to:
            {'lr': 0.0011,
            'gamma': 0.95,
            'dnd': {
                'size': 2000,
                'lr': 0.77,
                'sched': {
                    'end': 0.0,
                    'steps': 1000
            }}}
        """
        exp_dict = {}
        for key, value in flat_dict.items():
            if "." in key:
                keys = key.split(".")
                key_ = keys.pop(0)
                if key_ not in exp_dict:
                    exp_dict[key_] = Opt._expand_from_keys(keys, value)
                else:
                    exp_dict[key_] = Opt._recursive_update(
                        exp_dict[key_], Opt._expand_from_keys(keys, value)
                    )
            else:
                exp_dict[key] = value
        return Opt.from_dict(exp_dict)

    def to_flat_dict(self) -> dict:
        d = self.to_dict()
        return Opt._flatten_dict(d)

    def from_yaml(path: str | Path) -> "Opt":
        """Read a config file and return a namespace."""
        with open(path) as handler:
            config_data = yaml.load(handler, Loader=yaml.SafeLoader)
        return Opt.from_dict(config_data)

    def to_yaml(self, path: str | Path) -> None:
        d = Opt.sanitize_dict(self.to_dict())
        # TODO: figure out how to sanitize it.
        with open(Path(path), "w") as outfile:
            yaml.safe_dump(d, outfile, default_flow_style=False)

    @staticmethod
    def sanitize_dict(d: dict) -> dict:
        d_ = {}
        for k, v in d.items():
            if isinstance(v, dict):
                d_[k] = Opt.sanitize_dict(v)
            # ugly...
            elif not isinstance(v, (bool, int, float, str, list, tuple, dict)):
                d_[k] = str(v)
            else:
                d_[k] = v
        return d_

    @staticmethod
    def _flatten_dict(d: dict, prev_key: str = None) -> dict:
        """Recursive flatten a dict. Eg.: `{a: {ab: 0}}` -> `{a.ab: 0}`."""
        flat_dct: dict = {}
        for key, value in d.items():
            new_key = f"{prev_key}.{key}" if prev_key is not None else key
            if isinstance(value, dict):
                flat_dct.update(Opt._flatten_dict(value, prev_key=new_key))
            else:
                flat_dct[new_key] = value
        return flat_dct

    @staticmethod
    def _expand_from_keys(keys: list, value: object) -> dict:
        """Expand [a, b c] to {a: {b: {c: value}}}"""
        dct = d = {}
        while keys:
            key = keys.pop(0)
            d[key] = {} if keys else value
            d = d[key]
        return dct

    @staticmethod
    def _recursive_update(d: dict, u: dict) -> dict:
        "Recursively update `d` with stuff in `u`."
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = Opt._recursive_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    @staticmethod
    def _to_str(lopt: Self, indent: int = 0):
        s = ""
        for key, value in lopt.__dict__.items():
            if key.endswith("_"):
                continue
            s += f"{key:>{len(key) + indent}s}: "
            if isinstance(value, Opt):
                s += f"\n{Opt._to_str(value, indent + 2)}"
            else:
                s += f"{value}\n"
        return s

    def __str__(self):
        return Opt._to_str(self)


def main():
    d = {
        "a": 1,
        "b": {"ba": 1, "bb": 2},
        "c": {"ca": 1, "cb": 2, "cc": 3, "cd": {"cda_": 1, "cdb": {"x": 99, "y": 100}}},
    }
    opt = Opt.from_dict(d)
    print(isinstance(opt, Namespace))
    print(opt)
    print(repr(opt))

    fd = opt.to_flat_dict()
    print(fd)
    opt_ = Opt.from_flat_dict(fd)
    print(opt_)
    print(repr(opt_))

    return
    print("---")
    p = "results/2024Aug24-195848_hp_sweep/0000_optim.args_.eps_1e-06__optim.args_.lr_5e-05__agent.args_.target_update_freq_500__game_breakout/1/cfg.yaml"
    cfg = Opt.from_yaml(p)
    print(cfg)
    print(repr(cfg))


if __name__ == "__main__":
    main()
