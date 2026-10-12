"""Start the ShopEase development server on the loopback interface ONLY."""
import os
import sys
from app import create_app, ShopEaseRequestHandler

HOST = "127.0.0.1"
PORT = int(os.environ.get("SHOPEASE_PORT", "5000"))

if __name__ == "__main__":
    app = create_app()
    if not os.path.exists(app.config["DATABASE"]):
        sys.exit("Database not found. Run:  python -m app.init_db")
    print("ShopEase is a deliberately simple LOCAL training app. Do NOT expose it to a network or the internet.")
    # debug=False: the Werkzeug debugger allows code execution and must never be reachable.
    app.run(host=HOST, port=PORT, debug=False, request_handler=ShopEaseRequestHandler)
