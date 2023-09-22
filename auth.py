from flask import Flask, render_template, request, redirect, url_for,Blueprint

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')
@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    return 'this is a stub for a logout'##redirect(url_for('auth.login'))