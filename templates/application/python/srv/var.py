from environs import Env

env = Env()
env.read_env()

APPENV = env.str("APPENV", "dev")
PGHOST = env.str("PGHOST", "localhost")
PGPASS = env.str("PGPASS", "postgres")
PGUSER = env.str("PGUSER", "app")
PGDB = env.str("PGDB", "app")


def is_prod() -> bool:
    return APPENV.lower().startswith("prod")


def get_db_uri() -> str:
    return f"postgresql+psycopg2://{PGUSER}:{PGPASS}@{PGHOST}/{PGDB}"
