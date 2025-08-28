from hunter.api import create_app
from hunter.config import (
    PORT, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER)

print(PORT, NEO4J_USER, NEO4J_PASSWORD, NEO4J_URI)

app = create_app()

# app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)