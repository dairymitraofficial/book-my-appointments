from functools import wraps
from flask import session, redirect, flash

def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "owner":
            flash("Owner login required.", "error")
            return redirect("/owner/login")
        return f(*args, **kwargs)
    return decorated


def customer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "customer":
            flash("Customer login required.", "error")
            return redirect("/customer/login")
        return f(*args, **kwargs)
    return decorated
