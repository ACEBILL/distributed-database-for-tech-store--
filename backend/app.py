from flasgger import Swagger
from flask import Flask

from api.branch_api import branch_api_bp
from api.category_api import category_api_bp
from api.department_api import department_api_bp
from api.employee_api import employee_api_bp
from api.product_api import product_api_bp
from api.stats_api import stats_api_bp
from api.supplier_api import supplier_api_bp
from config import Config
from middleware.error_handler import register_error_handlers


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SWAGGER"] = {
        "title": "Tech Store Distributed Database API",
        "uiversion": 3,
        "openapi": "3.0.2",
        "specs_route": "/apidocs/",
    }

    app.register_blueprint(branch_api_bp)
    app.register_blueprint(category_api_bp)
    app.register_blueprint(department_api_bp)
    app.register_blueprint(employee_api_bp)
    app.register_blueprint(product_api_bp)
    app.register_blueprint(stats_api_bp)
    app.register_blueprint(supplier_api_bp)

    register_error_handlers(app)
    Swagger(app)

    @app.get("/swagger")
    def swagger_redirect():
        return {"message": "Swagger UI is available at /apidocs"}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
