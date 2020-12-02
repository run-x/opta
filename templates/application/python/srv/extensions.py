import logging
from typing import Any, Callable

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from srv.var import is_prod

db = SQLAlchemy()
migrate = Migrate()


def init_logger(app: Any) -> None:
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    root_logger = logging.getLogger()
    root_logger.setLevel(gunicorn_logger.level)


def init_extensions(app: Any) -> None:
    init_logger(app)
    db.init_app(app)
    migrate.init_app(app, db)
