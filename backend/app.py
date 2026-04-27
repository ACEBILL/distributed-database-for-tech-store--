from flask import Flask

from api.employee_api import employee_api_bp
from api.product_api import product_api_bp
from api.stats_api import stats_api_bp
from config import Config
from middleware.error_handler import register_error_handlers


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(employee_api_bp)
    app.register_blueprint(product_api_bp)
    app.register_blueprint(stats_api_bp)

    register_error_handlers(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
