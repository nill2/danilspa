'''
Process the auth requests
'''
from flask import render_template, Blueprint

'''
Process the auth requests
'''
from flask import render_template, Blueprint


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    '''
    a stub for login
    '''
    '''
    a stub for login
    '''
    return render_template('login.html')




@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    '''
    a stub for logout
    '''
    return 'this is a stub for a logout'  # redirect(url_for('auth.login'))
