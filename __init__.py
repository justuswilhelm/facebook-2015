from time import time
from functools import wraps
from os import getenv
from pickle import dumps, loads
from uuid import uuid4

from flask import (
    flash,
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from redis import Redis

application = Flask(__name__)
application.db = Redis.from_url(
    getenv('REDIS_URL', 'redis://localhost:6379/'))

application.secret_key = 'LOL'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@application.route("/")
def index():
    if application.db.exists(session.get('user')):
        return render_template('index.html')
    else:
        return redirect("register")


# Register
# Log In
@application.route("/register")
def register_get():
    return render_template('register.html')


@application.route("/register", methods=["post"])
def register_post():
    name = request.form['name']
    password = request.form['password']

    assert name != 'messages'
    assert name not in application.db

    application.db.set(name, password)
    session['user'] = name
    flash("Thank you for registering.")
    return redirect('/')


@application.route("/login")
def login_get():
    return render_template('login.html')


@application.route("/login", methods=['post'])
def login_post():
    name = request.form['name']
    password = request.form['password']

    if application.db.get(name).decode() == password:
        session['user'] = name
        flash("You were logged in successfully.")
        return redirect('/')
    else:
        flash("We were not able to log you in.")
        return redirect('/login')


@application.route("/messages", methods=['get'])
@login_required
def show_messages():
    messages = sorted(
        [loads(message) for _, message in
        application.db.hgetall('messages').items()],
        key=lambda e: e['time'],)
    return render_template('messages.html', messages=messages)


@application.route("/messages", methods=['post'])
@login_required
def post_message():
    message = request.form['message']

    message_object = {
        'time': time(),
        'message': message,
        'user': session['user'],
    }

    application.db.hset('messages', str(uuid4()), dumps(message_object))
    return redirect('/messages')
