from routes.auth import auth
from pymongo import MongoClient

from flask import Flask,render_template,jsonify,request

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

@app.route('/detail')
def detail():
    return render_template('detail.html')

if __name__ == "__main__":
    app.run(debug=True)
