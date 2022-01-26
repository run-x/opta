from os import environ
from sys import exit
from traceback import format_exc

from flask import Flask, json, jsonify, render_template, request
from flask_pymongo import PyMongo


def make_conn_string():

    MONGODB_URI = environ.get("MONGODB_URI", "")
    MONGODB_PASSWORD = environ.get("DB_PASSWORD", "")
    MONGODB_USER = environ.get("DB_USER", "")
    DATABASE_NAME = environ.get("DATABASE_NAME", "")

    if "" in set([MONGODB_URI, MONGODB_PASSWORD, MONGODB_USER]):
        print(
            "Are the 3 environment variables set? MONGO_URI, MONGO_PASSWORD, MONGO_USER"
        )
        exit(1)
    parts = MONGODB_URI.split("//")
    if DATABASE_NAME:
        rtnStr = "//".join(
            [
                parts[0],
                MONGODB_USER
                + ":"
                + MONGODB_PASSWORD
                + "@"
                + parts[1]
                + "/"
                + DATABASE_NAME
                + "?retryWrites=true&w=majority",
            ]
        )
    else:
        rtnStr = "//".join(
            [parts[0], MONGODB_USER + ":" + MONGODB_PASSWORD + "@" + parts[1]]
        )

    return rtnStr


MONGODB_CONN_STRING = make_conn_string()
app = Flask(__name__, static_url_path="")
app.config["MONGO_URI"] = MONGODB_CONN_STRING
mongodb = PyMongo(app)


@app.route("/")
def send_html():
    return render_template("index.html")


@app.route("/search", strict_slashes=False)
def search():
    query = request.args.get("arg")
    if not query:
        return []
    pipeline = [
        {
            "$search": {
                "text": {"query": query, "path": "fullplot"},
                "highlight": {"path": "fullplot"},
            }
        },
        {
            "$project": {
                "title": 1,
                "_id": 0,
                "year": 1,
                "fullplot": 1,
                "score": {"$meta": "searchScore"},
                "highlight": {"$meta": "searchHighlights"},
            }
        },
        {"$limit": 10},
    ]
    results = mongodb.db.movies.aggregate(pipeline)

    resp = jsonify(list(results))
    return resp
