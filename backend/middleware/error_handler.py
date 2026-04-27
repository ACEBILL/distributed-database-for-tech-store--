from flask import jsonify, request


def register_error_handlers(app):
    @app.errorhandler(ValueError)
    def handle_value_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": str(error)}), 400

        return str(error), 400

    @app.errorhandler(500)
    def handle_internal_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500

        return "Internal server error", 500
