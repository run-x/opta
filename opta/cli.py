import os
from typing import Any, Iterable, Mapping

import click
import yaml
from module import Env, Module


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--inp", default="opta.yml", help="Opta config file")
@click.option("--out", default="main.tf.json", help="Generated tf file")
def gen(inp: str, out: str) -> None:
    """ Generate TF file based on opta config file """
    if not os.path.exists(inp):
        raise Exception(f"File {inp} not found")

    conf = yaml.load(open(inp), Loader=yaml.Loader)
    # Top level objects are resources. Each will lead to a module block
    # Providers are provided by env module (via a providers.tfx file).
    # For env, they're defined in the yaml
    # Backend should be hardcoded based on name
    # Re-export all env outputs. Any module can re-use them as input with the same name
    # TODO Add dependancy

    meta = conf.pop("meta")

    if "create-env" in meta:
        if len(conf.keys()) != 1:
            raise Exception("Multiple environments in file")

        # key = list(conf.keys())[0]
        # env = EnvModule(meta, key, conf[key])

        # gen_tf(env.gen_blocks(), out)
    else:
        if not os.path.exists(meta["env"]):
            raise Exception(f"Env {meta['env']} not found")

        env_conf = yaml.load(open(meta["env"]), Loader=yaml.Loader)
        env = Env(env_conf)

        gen_tf(
            env.gen_env_blocks()
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
