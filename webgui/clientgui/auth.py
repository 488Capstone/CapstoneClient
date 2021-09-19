import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from clientgui.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
# when user visits /auth/register URL, this register view will return HTML with form to fill out. When form submitted we'll validate.
def register():
    # If the user submitted the form, request.method will be 'POST'. In this case, start validating the input.
    if request.method == 'POST':
        #get the values of username and pw from the html form
        #request.form is a special type of dict mapping submitted form keys and values.
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        # if they're empty, throw an error and loop back to login
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                # add the uname and pw to our db
                # the pw is hashed with gen_pw_hash() func below
                #since we're in development, we don't want users to be able to register new acc's after the first
                solo_user = db.execute(
                    'SELECT * FROM user'
                ).fetchone()
                if solo_user is None:
                    db.execute(
                        "INSERT INTO user (username, password) VALUES (?, ?)",
                        (username, generate_password_hash(password)),
                    )
                    # save the changes to db
                    db.commit()
                else:
                    error = f"Proj in DEV mode, only 1 registered user allowed. The 1 user is already registered. Contact DW for login Creds"
                    flash(error)

            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                # redirect back to the login page?
                return redirect(url_for("auth.login"))

        #If validation fails, the error is shown to the user. flash() stores messages that can be retrieved when rendering the template.
        flash(error)

# When the user initially navigates to auth/register, or there was a validation error, an HTML page with the registration form should be shown. render_template() will render a template containing the HTML, which you’ll write in the next step of the tutorial.

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        # fetchone() returns one row from the query. If the query returned no results, it returns None. Later, fetchall() will be used, which returns a list of all results.

        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

# session is a dict that stores data across requests. When validation succeeds, the user’s id is stored in a new session. The data is stored in a cookie that is sent to the browser, and the browser then sends it back with subsequent requests. Flask securely signs the data so that it can’t be tampered with.

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('main.home'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('first_page'))

#require login for all other views
#This decorator returns a new view function that wraps the original view it’s applied to. The new function checks if a user is loaded and redirects to the login page otherwise. If a user is loaded the original view is called and continues normally. You’ll use this decorator when writing the blog views.
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


