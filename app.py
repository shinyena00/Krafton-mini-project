from routes.auth import auth
from bson import ObjectId
from pymongo import MongoClient

from flask import Flask,render_template,jsonify,request
from flask.json.provider import JSONProvider

app = Flask(__name__)
app.register_blueprint(auth)

client=MongoClient('localhost',27017)
db = client["jungle_errand"]
errands = db["errands"]

@app.route('/')
def home():
    errand_list = errands.find({'status':'OPEN'})
    return render_template('index.html',errands=errand_list)

@app.route('/new_errand')
def new_errand():
    return render_template('new_errand.html') 

# @app.route('/')
# def post_errand():

#   errands={'title':title_receive,'image':image_url,'status':status_receive,'time':time_receive,'location':location_receive,'reward':reward_receive,'register_id':register_receive,'accepter':accept_receive}
#   function showerrand(){
#     $.ajax({
#         type: "GET",
#         url:"/memo",
#         data: {},
#         success: function(response){
#             let errand=response["errand"];
#             console.log(errand);
#             for(let i=0 ; i<errand.length ; i++){
            
#         }
#         }
#     });
#} 
#    request.form['url']
#  

@app.route('/errand',methods=['POST'])
def post_errand():
    title_receive=request.form['title_give']
    description_receive=request.form['description_give']
    place_receive=request.form['place_give']
    period_receive=request.form['period_give']
    point_receive=request.form['point_give']
    errand={'title':title_receive,'location':place_receive, 'time':period_receive ,'reward':point_receive,'status':'OPEN'}
    errands.insert_one(errand)
    return jsonify({'result': 'success'})

@app.route('/errand',methods=['GET'])
def search_errand():
    result=list(errands.find({},{'_id':0}))
    return jsonify({'point':result})

# @app.route('/login')
# def login():
#     return render_template('login.html') 

# @app.route('/signup')
# def signup():
#     return render_template('signup.html') 

@app.route('/detail')
def detail():
    return render_template('detail.html')

# @app.route('/mypage')
# def mypage():
#     return render_template('mypage.html') 




# {
#   "user": {
#     "user_id": "user_1024",                   // 문자열 (고유 식별자)
#     "nickname": "용인번개",              // 문자열
#     "password": "hashed_password_123",   // 문자열 (비밀번호는 암호화 문자열)
#     "registered_list": ["errand_5892"],      // 배열 (등록한 심부름 목록)
#     "accepteded_list": ["errand_8999"],      // 배열 (수락한 심부름 목록)
#     "point": 33                          // 숫자 (포인트/수치)
#   },
#   "errand": {
#     "errand_id": "errand_5892",          // 문자열 또는 숫자
#     "title": "편의점에서 감기약 좀 사다주세요", // 문자열
#     "image": "https://example.com/img.jpg", // 문자열 (이미지 URL 경로)
#     "status": "MATCHED",                 // 문자열 (상태값: REQUESTED, MATCHED, DONE)
#     "time": "2026-08-25T15:30:00",       // 문자열 (날짜/시간 ISO 표준)
#     "location": "경기도 용인시 수지구",  // 문자열 (주소)
#     "reward": 500,                     // 숫자 (보수 금액)
#     "register_id": "user_1024",          // 문자열 (등록한 유저 ID)
#     "accepter_id": "user_2048"             // 문자열 (수락한 유저 ID, 오타 수정)
#   }
# }
if __name__ == "__main__":
    app.run(debug=True)
