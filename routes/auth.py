from flask import render_template, request, redirect, url_for, make_response, jsonify, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
from bson.objectid import ObjectId

from db import users_collection, errands_collection
from image_utils import save_uploaded_image

auth = Blueprint("auth", __name__)

load_dotenv()
SECRET_KEY = os.environ["JWT_SECRET_KEY"]

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        loginid = request.form["loginid"]
        loginpassword = request.form["loginpassword"]

        user = users_collection.find_one({"userid" : loginid})

        if not user:
            return {"success" : False}

        if not check_password_hash(user['password'], loginpassword):
            return {"success" : False}

        else:
            payload = {
                "user_id" : str(user["_id"]),
                "exp" : datetime.now(timezone.utc) + timedelta(hours=24)
            }

            token = jwt.encode(
                payload,
                SECRET_KEY,
                algorithm="HS256"
            )

            response = make_response(
                jsonify({"success": True})
            )

            response.set_cookie(
                "token",
                token,
                httponly=True
            )
            return response


    return render_template("login.html")

@auth.route("/check-nickname", methods=["POST"])
def check_nickname():
    nickname = request.form["nickname"]

    user = users_collection.find_one({"nickname" : nickname})

    if user:
        return {"available" : False}
    else:
        return {"available" : True}

@auth.route("/check-id", methods=["POST"])
def check_id():
    userid = request.form["userid"]

    user = users_collection.find_one({"userid" : userid})

    if user:
        return {"available" : False}
    else:
        return {"available" : True}


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        userid = request.form["user_id"]
        nickname = request.form["user_nickname"]
        password = request.form["user_password"]
        password_confirm = request.form["user_password_confirm"]

        if(password != password_confirm):
            return render_template(
                "signup.html",
                error="비밀번호가 서로 일치하지 않습니다."
            )

        if(users_collection.find_one({"$or": [{"userid" : userid}, {"nickname": nickname}]})):
           return render_template(
               "signup.html",
               error="이미 사용 중인 아이디 또는 닉네임입니다."
           )

        profile_image, image_error = save_uploaded_image(
            request.files.get("profile_image")
        )

        if image_error:
            return render_template(
                "signup.html",
                error=image_error
            )

        password_hash = generate_password_hash(password)
        doc = {
            'userid' : userid,
            'nickname' : nickname,
            'password' : password_hash,
            'point' : 10,
            'profile_image': profile_image,
        }
        users_collection.insert_one(doc)
        return redirect(url_for("auth.login"))

    return render_template("signup.html")

        
def get_current_user():
    token = request.cookies.get("token")

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        user_id = payload["user_id"]

        user = users_collection.find_one({"_id": ObjectId(user_id)})

        return user
    
    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None

@auth.route("/mypage")
def mypage():
    user = get_current_user()

    if not user:
        return """
        <script>
            alert("로그인을 먼저 진행해주세요.\\n 확인을 누르면 로그인 창으로 이동합니다.")
            window.location.href = "/login";
        </script>
        """

    requested_errands = list(
        errands_collection.find({
            "requester_id": user["_id"]
        }).sort("created_at", -1)
    )

    accepted_errands = list(
        errands_collection.find({
            "worker_id": user["_id"]
        }).sort("created_at", -1)
    )

    return render_template(
        "mypage.html",
        user=user,
        requested_errands=requested_errands,
        accepted_errands=accepted_errands
    )

@auth.route("/logout")
def logout():
    response = redirect(url_for("auth.login"))
    response.delete_cookie("token")
    return response

