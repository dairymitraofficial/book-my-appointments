from flask import Blueprint, render_template, session, redirect
from extensions import get_db
from utils.security import owner_required

owner_account_bp = Blueprint("owner_account", __name__)

@owner_account_bp.route("/owner/account")
@owner_required
def owner_account():


    return redirect("/owner/dashboard")

