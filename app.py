from flask import Flask, render_template, request, make_response
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.presentation.routes.mining import mining_bp
import os
import json

app = Flask(__name__)

# Internationalization
TRANSLATIONS = {}
def load_translations():
    trans_dir = 'translations'
    if not os.path.exists(trans_dir):
        return
    for lang_file in os.listdir(trans_dir):
        if lang_file.endswith('.json'):
            lang_code = lang_file.split('.')[0]
            with open(os.path.join(trans_dir, lang_file), 'r', encoding='utf-8') as f:
                TRANSLATIONS[lang_code] = json.load(f)

load_translations()

def get_locale():
    # Priority: query param > cookie > default
    lang = request.args.get('lang')
    if lang:
        return lang
    return request.cookies.get('lang', 'en')

@app.context_processor
def inject_translate():
    lang = get_locale()
    # Ensure we have a dictionary for the current language, fallback to English then to empty
    en_translations = TRANSLATIONS.get('en', {})
    lang_translations = TRANSLATIONS.get(lang, en_translations)
    
    # In case TRANSLATIONS.get returned None for some reason
    if lang_translations is None:
        lang_translations = en_translations or {}
    
    def _(key):
        return lang_translations.get(key, key)
        
    return {'_': _, 'current_lang': lang, 'all_translations': lang_translations}

@app.route('/set_lang/<lang>')
def set_lang(lang):
    response = make_response("Language set")
    response.set_cookie('lang', lang, max_age=60*60*24*30) # 30 days
    # Return to referrer if possible
    referrer = request.referrer or '/'
    response.headers['Location'] = referrer
    return response, 302

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
    app.run(debug=True, port=8000)
