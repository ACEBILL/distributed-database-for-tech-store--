import pymysql
import pyodbc
from flask import jsonify, request


SQLSERVER_DUPLICATE_KEY_CODES = {"2627", "2601"}
SQLSERVER_FOREIGN_KEY_CODE = "547"
MYSQL_DUPLICATE_KEY_CODE = "1062"
MYSQL_FOREIGN_KEY_CODES = {"1451", "1452"}


def _classify_integrity_error(error):
    message = str(error)
    if any(code in message for code in SQLSERVER_DUPLICATE_KEY_CODES):
        return 409, "Duplicate key"
    if SQLSERVER_FOREIGN_KEY_CODE in message:
        return 409, "Foreign key constraint violated"
    if MYSQL_DUPLICATE_KEY_CODE in message:
        return 409, "Duplicate key"
    if any(code in message for code in MYSQL_FOREIGN_KEY_CODES):
        return 409, "Foreign key constraint violated"
    return 400, "Database integrity error"


def register_error_handlers(app):
    @app.errorhandler(ValueError)
    def handle_value_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": str(error)}), 400

        return str(error), 400

    @app.errorhandler(pyodbc.IntegrityError)
    def handle_integrity_error(error):
        status, label = _classify_integrity_error(error)
        if request.path.startswith("/api/"):
            return jsonify({"error": label, "detail": str(error)}), status

        return f"{label}: {error}", status

    @app.errorhandler(pymysql.err.IntegrityError)
    def handle_mysql_integrity_error(error):
        status, label = _classify_integrity_error(error)
        if request.path.startswith("/api/"):
            return jsonify({"error": label, "detail": str(error)}), status

        return f"{label}: {error}", status

    @app.errorhandler(500)
    def handle_internal_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500

        return "Internal server error", 500
