# extensions.py

import mysql.connector
from flask import g, current_app
from flask_jwt_extended import JWTManager
from flask_wtf import CSRFProtect

jwt = JWTManager()
csrf = CSRFProtect()   # ✅ THIS WAS MISSING


def db_init(app):
    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()


def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            autocommit=False
        )
    return g.db
