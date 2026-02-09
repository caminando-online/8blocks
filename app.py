from flask import Flask, render_template
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.presentation.routes.mining import mining_bp
import os

app = Flask(__name__)

# Security configuration
talisman = Talisman(app, 
                    content_security_policy=None,  # Adjust as needed
                    force_https=False)  # Local development

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["1000 per day", "500 per hour"]
)


# Register Blueprints
app.register_blueprint(mining_bp)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
