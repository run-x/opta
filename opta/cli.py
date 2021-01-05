import os
import subprocess
from typing import Any

import click
import yaml

from os import path
from opta import gen_tf
from opta.module import Env, Module
from opta.plugins.link_processor import LinkProcessor
from opta.utils import deep_merge


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.pass_context
@click.option("--inp", default="opta.yml", help="Opta config file")
@click.option("--out", default="main.tf.json", help="Generated tf file")
@click.option("--init", is_flag=True, default=False, help="Generate init tf file")
def apply(ctx: Any, inp: str, out: str, init: bool) -> None:
    ctx.forward(gen)
    subprocess.run(["terraform", "init"], check=True)
    subprocess.run(["terraform", "apply"], check=True)


@cli.command()
@click.option("--configfile", default="opta.yml", help="Opta config file")
@click.option("--lockfile", default="opta.lock", help="Opta config file")
@click.option("--out", default="main.tf.json", help="Generated tf file")
@click.option("--init", is_flag=True, default=False, help="Generate init tf file")
def gen(configfile: str, lockfile: str, out: str, init: bool) -> None:
    """ Generate TF file based on opta config file """
    if not os.path.exists(configfile):
        raise Exception(f"File {configfile} not found")

    conf = yaml.load(open(configfile), Loader=yaml.Loader)
    lockdata = (
        yaml.load(open(lockfile), Loader=yaml.Loader) if path.exists(lockfile) else dict()
    )

    meta = conf.pop("meta")

    if "create-env" in meta:
        env = Env(meta, conf)

        if init:
            gen_tf.gen(env.gen_providers(init), out)
        else:
            gen_tf.gen(deep_merge(env.gen_blocks(), env.gen_providers(init)), out)
    else:
        if not os.path.exists(meta["env"]):
            raise Exception(f"Env {meta['env']} not found")

        env_conf = yaml.load(open(meta["env"]), Loader=yaml.Loader)
        env_meta = env_conf.pop("meta")

        env = Env(env_meta, env_conf, child_meta=meta)

        ret = env.gen_providers(init)
        modules = list(map(lambda key: Module(meta, key, conf[key], env), conf.keys()))
        LinkProcessor().process(modules)

        for module in modules:
            ret = deep_merge(module.gen_blocks(), ret)

        gen_tf.gen(ret, out)

    print("Writing lockfile...")
    with open(lockfile, "w") as f:
        f.write(yaml.dump(lockdata))


if __name__ == "__main__":
    cli()
