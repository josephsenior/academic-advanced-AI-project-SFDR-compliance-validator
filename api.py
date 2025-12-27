"""
REST API for Document Validation System
Modern API endpoints for frontend integration
"""

from __future__ import annotations

import os

from server import create_app


# Thin entrypoint: the API is implemented in the `server` package.
app = create_app()


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=False, host=host, port=port, threaded=True, use_reloader=False)

