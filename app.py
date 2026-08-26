from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.environ["JWT_SECRET_KEY"]

client = MongoClient("mongodb://localhost:27017/")
db = client["jungle_errand"]
users = db["users"]
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        loginid = request.form["loginid"]
        loginpassword = request.form["loginpassword"]

        user = users.find_one({"userid" : loginid})

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

@app.route("/check-nickname", methods=["POST"])
def check_nickname():
    nickname = request.form["nickname"]

    user = users.find_one({"nickname" : nickname})

    if user:
        return {"available" : False}
    else:
        return {"available" : True}

@app.route("/check-id", methods=["POST"])
def check_id():
    userid = request.form["userid"]

    user = users.find_one({"userid" : userid})

    if user:
        return {"available" : False}
    else:
        return {"available" : True}


@app.route("/signup", methods=["GET", "POST"])
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

        if(users.find_one({"$or": [{"userid" : userid}, {"nickname": nickname}]})):
           return render_template(
               "signup.html",
               error="이미 사용 중인 아이디 또는 닉네임입니다."
           )

        password_hash = generate_password_hash(password)
        doc = {
            'userid' : userid,
            'nickname' : nickname,
            'password' : password_hash,
            'point' : 10,
        }
        db.users.insert_one(doc)
        return redirect(url_for("login"))

    return render_template("signup.html")

        
def get_current_user_id():
    token = request.cookies.get("token")

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        return payload["user_id"]
    
    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None



if __name__ == "__main__":
    app.run(debug=True)