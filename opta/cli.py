import os

import click
import gen_tf
import yaml
from module import Env, Module
from plugins.link_processor import LinkProcessor
from utils import deep_merge


@click.group()
def cli() -> None:
    pass


# TODO
# [x] Generate provider from env
# [x] k8s provider hackx
# [x] Convert to tf format
# [x] Create tf state for env
# [x] Handle db password
# [x] How would deployment work
# [ ] Linking post processor
# [ ] Support remote state


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

        gen_tf.gen(deep_merge(env.gen_blocks(), env.gen_providers()), out)
    else:
        if not os.path.exists(meta["env"]):
            raise Exception(f"Env {meta['env']} not found")

        env_conf = yaml.load(open(meta["env"]), Loader=yaml.Loader)
        env_meta = env_conf.pop("meta")

        env = Env(env_meta, env_conf, path=meta["env"])

        ret = deep_merge(env.gen_providers(include_derived=True), env.gen_remote_state())
        modules = list(map(lambda key: Module(meta, key, conf[key], env), conf.keys()))
        LinkProcessor().process(modules)

        for module in modules:
            ret = deep_merge(module.gen_blocks(), ret)

        gen_tf.gen(ret, out)


if __name__ == "__main__":
    cli()
