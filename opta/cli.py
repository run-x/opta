import os
from typing import Any, Iterable, Mapping

import click
import yaml
from module import Env, Module


@click.group()
def cli() -> None:
    pass


# TODO
# [x] Generate provider from env
# [x] k8s provider hackx
# [ ] Linking post processor
# [ ] Handle db password
# [ ] Convert to tf format
# [ ] How would deployment work


@cli.command()
@click.option("--inp", default="opta.yml", help="Opta config file")
@click.option("--out", default="main.tf.json", help="Generated tf file")
def gen(inp: str, out: str) -> None:
    """ Generate TF file based on opta config file """
    if not os.path.exists(inp):
        raise Exception(f"File {inp} not found")

    conf = yaml.load(open(inp), Loader=yaml.Loader)

    meta = conf.pop("meta")

    if "create-env" in meta:
        env = Env(meta, conf)

        gen_tf(env.gen_providers() + env.gen_blocks(), out)
    else:
        if not os.path.exists(meta["env"]):
            raise Exception(f"Env {meta['env']} not found")

        env_conf = yaml.load(open(meta["env"]), Loader=yaml.Loader)
        env_meta = env_conf.pop("meta")

        env = Env(env_meta, env_conf)

        gen_tf(
            env.gen_providers(include_derived=True)
            + [
                blk
                for module_key in conf.keys()
                for blk in Module(meta, module_key, conf[module_key], env).gen_blocks()
            ],
            out,
        )


def gen_tf(blocks: Iterable[Mapping[Any, Any]], out_file: str) -> None:
    print(blocks)
    print(f"Output written to {out_file}")


if __name__ == "__main__":
    cli()
