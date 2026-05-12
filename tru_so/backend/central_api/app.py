from datetime import datetime, timedelta, timezone

from flasgger import Swagger
from flask import Flask
import jwt

from central_api.api.auth_api import auth_api_bp
from central_api.api.branch_replication_api import branch_replication_api_bp
from central_api.api.branch_api import branch_api_bp
from central_api.api.category_api import category_api_bp
from central_api.api.department_api import department_api_bp
from central_api.api.employee_api import employee_api_bp
from central_api.api.invoice_api import invoice_api_bp
from central_api.api.product_api import product_api_bp
from central_api.api.stats_api import stats_api_bp
from central_api.api.supplier_api import supplier_api_bp
from central_api.api.system_api import system_api_bp
from config import Config
from middleware.error_handler import register_error_handlers
from services.failover_health_monitor import start_failover_monitor


def _swagger_ui_params_text(app):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "swagger-demo",
            "ho_ten": "Swagger Demo",
            "chuc_vu": "admin",
            "ma_phong_ban": None,
            "scope": "central",
            "branch_code": None,
            "source_engine": app.config["DB_ENGINE"],
            "iat": now,
            "exp": now + timedelta(hours=app.config["JWT_EXPIRES_HOURS"]),
        },
        app.config["JWT_SECRET"],
        algorithm=app.config["JWT_ALGORITHM"],
    )
    return """
{
    persistAuthorization: true,
    requestInterceptor: function(request) {
        request.headers = request.headers || {};
        var token = window.localStorage.getItem("techstore_swagger_token") || "%s";
        if (token) {
            request.headers["Authorization"] = "Bearer " + token;
        }
        return request;
    },
    responseInterceptor: function(response) {
        try {
            var token = response && response.obj && response.obj.token;
            if (!token && response && response.text) {
                token = JSON.parse(response.text).token;
            }
            if (token) {
                window.localStorage.setItem("techstore_swagger_token", token);
            }
        } catch (error) {}
        return response;
    }
}
""" % token


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
    app.config["SWAGGER"]["ui_params_text"] = _swagger_ui_params_text(app)

    app.register_blueprint(auth_api_bp)
    app.register_blueprint(branch_replication_api_bp)
    app.register_blueprint(branch_api_bp)
    app.register_blueprint(category_api_bp)
    app.register_blueprint(department_api_bp)
    app.register_blueprint(employee_api_bp)
    app.register_blueprint(invoice_api_bp)
    app.register_blueprint(product_api_bp)
    app.register_blueprint(stats_api_bp)
    app.register_blueprint(supplier_api_bp)
    app.register_blueprint(system_api_bp)

    register_error_handlers(app)
    Swagger(app)

    @app.get("/api/ping")
    @app.get("/api/tru-so/ping")
    def ping():
        return {"service": "central-api", "status": "ok"}

    start_failover_monitor(app)

    return app


app = create_app()
