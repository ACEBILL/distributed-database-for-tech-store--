from flasgger import Swagger
from flask import Flask

from central_api.api.auth_api import auth_api_bp
from central_api.api.branch_api import branch_api_bp
from central_api.api.category_api import category_api_bp
from central_api.api.department_api import department_api_bp
from central_api.api.employee_api import employee_api_bp
from central_api.api.product_api import product_api_bp
from central_api.api.stats_api import stats_api_bp
from central_api.api.supplier_api import supplier_api_bp
from config import Config
from middleware.error_handler import register_error_handlers


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["APP_ROLE"] = "central"
    app.config["SWAGGER"] = {
        "title": "Tech Store Central API",
        "uiversion": 3,
        "openapi": "3.0.2",
        "specs_route": "/apidocs/",
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        },
    }

    app.register_blueprint(auth_api_bp)
    app.register_blueprint(branch_api_bp)
    app.register_blueprint(category_api_bp)
    app.register_blueprint(department_api_bp)
    app.register_blueprint(employee_api_bp)
    app.register_blueprint(product_api_bp)
    app.register_blueprint(stats_api_bp)
    app.register_blueprint(supplier_api_bp)

    register_error_handlers(app)
    Swagger(app)

    @app.get("/api/ping")
    def ping():
        return {"service": "central-api", "status": "ok"}

    return app


app = create_app()
