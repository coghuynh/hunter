from hunter.api import create_app
from hunter.config import PORT

app = create_app()

# app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(port=PORT, debug=True)