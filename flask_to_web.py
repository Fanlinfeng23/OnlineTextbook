"""Deprecated entrypoint kept for backward compatibility.

Prefer using ``app.py`` or invoking ``online_textbook.create_app`` directly.
"""

import os

from online_textbook import create_app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)