from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    # Enable debugging mode
    app.debug = True
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    return app