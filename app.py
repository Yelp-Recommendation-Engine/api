#!flask/bin/python
from flask import Flask, jsonify, request, make_response
from flask.ext.cors import CORS
import pymongo 
import json 
import re
from pymongo import MongoClient
from bson import BSON
from bson import json_util

connection = MongoClient("mongodb://localhost:27017")

db = connection.recommender 

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/searchRestaurants', methods=['GET', 'POST'])
def get_restaurants_by_name():
    coll = db.businesses
    data = json.loads(request.data)
    businesses = coll.find( { "name": {"$regex": re.compile(u''+ data['name'], re.IGNORECASE) }})
    resp = make_response(json.dumps(list(businesses), sort_keys=True, indent=4, default=json_util.default))
    return resp

if __name__ == '__main__':
    app.run(debug=True)
    
