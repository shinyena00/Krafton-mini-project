from bson import Object
from pymongo import MongoClient

from flask import Flask,render_template,jsonify,request
from flask.json.provider import JSONProvider

import json
import sys

app=Flask(__name__)
client=MongoClient('localhost',27017)
db=client.dbkrafton_erand

@app.route('/')
def home():
    return render_template('index.html')
 
@app.route('/login')
def login():
    return render_template('login.html') 

@app.route('/signup')
def signup():
    return render_template('signup.html') 

@app.route('/detail')
def detail():
    return render_template('detail.html') 

@app.route('/mypage')
def mypage():
    return render_template('mypage.html') 

@app.route('/new_errand')
def new_errand():
    return render_template('new_errand.html') 