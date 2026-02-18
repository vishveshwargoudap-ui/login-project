from functools import wraps
from flask import session, redirect,url_for

def login_required(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        if'email'not in session:
            return redirect('/login')
        return f(*args,**kwargs)
    return wrapper
        