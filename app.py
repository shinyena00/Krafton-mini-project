from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["jungle_errand"]
users = db["users"]
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
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
        

        doc = {
            'userid' : userid,
            'nickname' : nickname,
            'password' : password,
            'point' : 10,
        }
        db.users.insert_one(doc)
        return redirect(url_for("login"))

    return render_template("/signup.html")

        





if __name__ == "__main__":
    app.run(debug=True)