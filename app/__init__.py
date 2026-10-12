import os
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from werkzeug.serving import WSGIRequestHandler
from .db import close_db
from .errors import ApiError

class ShopEaseRequestHandler(WSGIRequestHandler):
    """Dev-server handler that does not advertise Werkzeug/Python versions in the Server header."""

    def version_string(self):
        return "ShopEase"


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("SHOPEASE_DATABASE", os.path.join(BASE_DIR, "instance", "shopease.db")),
        COOKIE_SECURE=os.environ.get("SHOPEASE_COOKIE_SECURE", "0") == "1",
        SESSION_TTL_SECONDS=3600,
        PASSWORD_HASH_METHOD=os.environ.get("SHOPEASE_HASH_METHOD", "scrypt"),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if config:
        app.config.update(config)

    from .api import bp as api_bp
    from .pages import bp as pages_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)
    app.teardown_appcontext(close_db)

    @app.errorhandler(ApiError)
    def handle_api_error(e):
        body = {"error": {"code": e.code, "message": e.message}}
        if e.fields:
            body["error"]["fields"] = e.fields
        return jsonify(body), e.status

    @app.errorhandler(Exception)
    def handle_any(e):
        if isinstance(e, HTTPException):
            names = {400: "bad_request", 404: "not_found", 405: "method_not_allowed",
                     413: "payload_too_large", 415: "unsupported_media_type"}
            resp = jsonify({"error": {"code": names.get(e.code, "http_error"), "message": e.name}})
            resp.status_code = e.code
            for k, v in e.get_headers():
                if k.lower() == "allow":
                    resp.headers[k] = v
            return resp
        app.logger.exception("Unhandled error")  # details go to the server log only
        return jsonify({"error": {"code": "server_error", "message": "Internal server error."}}), 500

    @app.after_request
    def security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        if resp.mimetype == "application/json":
            resp.headers["Cache-Control"] = "no-store"
        return resp

    return app
