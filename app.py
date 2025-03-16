from flask import Flask
from flask_cors import CORS
from database import init_db
from api import api_bp
from ui import ui_bp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(api_bp)
app.register_blueprint(ui_bp)

# Initialize database on startup
@app.before_first_request
def before_first_request():
    init_db()

if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
