'''
This is a initialization function
'''
from flask import Flask
from .main import main as main_blueprint
from .auth import auth as auth_blueprint


def create_app():  # test_config=None
    '''
    Create application and define blueprints
    '''
    app = Flask(__name__, instance_relative_config=True)

    # Enable debugging mode
    app.debug = True

    app.register_blueprint(main_blueprint)

    app.register_blueprint(auth_blueprint)

    return app
