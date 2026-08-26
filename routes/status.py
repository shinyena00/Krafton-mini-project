from flask import render_template, request, redirect, url_for, make_response, jsonify, Blueprint
from pymongo import MongoClient
from routes.auth import get_current_user

status = Blueprint("stauts", __name__)

@status.route("/errand/<errand_id>/accept", methods=["POST"])
def accept_errand(errand_id):
    user = get_current_user()

    if not user:
        return{
            "success": False,
            "message": "로그인이 필요합니다."
        }
