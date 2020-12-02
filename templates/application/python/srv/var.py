from environs import Env

env = Env()
env.read_env()

APPENV = env.str("APPENV", "dev")
PGHOST = env.str("PGHOST", "localhost")
PGPASS = env.str("PGPASS", "postgres")
PGUSER = env.str("PGUSER", "postgres")
PGDB = env.str("PGDB", "main")


def is_prod() -> bool:
    return APPENV.lower().startswith("prod")


def get_postgres_password() -> str:
    if is_prod():
        return "WHAT"
    return "postgres"


def get_db_uri() -> str:
    return f"postgresql+psycopg2://{PGUSER}:{PGPASS}@{PGHOST}/{PGDB}"
