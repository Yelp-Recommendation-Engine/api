#!flask/bin/python
from flask import Flask, jsonify, request, make_response
from flask.ext.cors import CORS
import pymongo 
import json 
import re
import datetime
from pymongo import MongoClient
from bson import BSON
from bson import json_util

connection = MongoClient("mongodb://localhost:27017")
db = connection.recommender 

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/rateRestaurant', methods=['POST'])
def rate_restaurant():
    reviews = db.reviews
    business_ratings = db.business_ratings
    user_ratings = db.user_ratings
    rating_data = json.loads(request.data)
    rating = rating_data["rating"]
    user_id = rating_data["user_id"]
    business_id = rating_data["business_id"]

    reviews.insert( { "user_id": user_id, "business_id": business_id, "stars": rating, "date": datetime.datetime.now()})
    user_business = user_id + "." + business_id
    user_ratings.update( {"_id": user_id}, { "$set": { user_business: rating}})
    business_user = business_id + "." + user_id
    business_ratings.update( {"_id": business_id}, { "$set": { business_user: rating}})

    resp = make_response("", 201)
    return resp

@app.route('/searchRestaurants', methods=['GET', 'POST'])
def get_restaurants_by_name():
    coll = db.businesses
    data = json.loads(request.data)
    businesses = coll.find( { "name": {"$regex": re.compile(u''+ data['name'], re.IGNORECASE) }})
    resp = make_response(json.dumps(list(businesses), sort_keys=True, indent=4, default=json_util.default))
    return resp

if __name__ == '__main__':
    app.run(debug=True)
    
