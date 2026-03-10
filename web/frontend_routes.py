import os
from flask import Blueprint, render_template, request, session, redirect, url_for
from functools import wraps

frontend_bp = Blueprint('frontend', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('frontend.login'))
        return f(*args, **kwargs)
    return decorated_function

@frontend_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        global_pwd = os.environ.get('GLOBAL_PASSWORD')

        # If GLOBAL_PASSWORD is set, we check against it.
        # If it is NOT set, we bypass authentication for local dev convenience,
        # but warn the user.
        if not global_pwd:
             print("WARNING: GLOBAL_PASSWORD not set. Allowing access without password check.")
             session['authenticated'] = True
             return redirect(url_for('frontend.index'))

        if password == global_pwd:
            session['authenticated'] = True
            return redirect(url_for('frontend.index'))
        else:
            return render_template('login.html', error="Invalid Password")

    return render_template('login.html')

@frontend_bp.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('frontend.login'))

@frontend_bp.route('/')
@login_required
def index():
    """Renders the main chat interface."""
    return render_template('index.html')
