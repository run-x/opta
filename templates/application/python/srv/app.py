from typing import Union

from flask import Flask

from srv import var
from srv.extensions import init_extensions

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = var.get_db_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
init_extensions(app)

@app.route("/")
def healthcheck() -> str:
    return "hello world!"
