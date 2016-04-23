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
from recommendations import getRecommendations

connection = MongoClient("mongodb://localhost:27017")
db = connection.recommender

db = connection.users

reviews = db.reviews

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/getRecommendations', methods=['POST'])
def get_recommendations():
    user_data = json.loads(request.data)
    items = getRecommendations(user_data["user_id"])
    resp = make_response(json.dumps(list(items), sort_keys=True, indent=4, default=json_util.default))
    return resp

@app.route('/getRatedRestaurants', methods=['POST'])
def get_rated_restaurants():
    user_data = json.loads(request.data)
    user_id = user_data["user_id"]
    restaurants = reviews.find({"user_id": user_id})#.sort([("date", -1)])
    resp = make_response(json.dumps(list(restaurants), sort_keys=True, indent=4, default=json_util.default))
    return resp

@app.route('/rateRestaurant', methods=['POST'])
def rate_restaurant():
    business_ratings = db.business_ratings
    user_ratings = db.user_ratings
    rating_data = json.loads(request.data)
    rating_data["date"] =  datetime.datetime.now()
    rating = rating_data["stars"]
    user_id = rating_data["user_id"]
    business_id = rating_data["business_id"]
    
    reviews.insert(rating_data)
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


#services for registering users
@app.route('/authenticateUser', methods=['POST'])
def authenticate_user():
    print("Service has been called")
    coll = db.users
    data = json.loads(request.data.decode('utf-8'))

    cursor = db.userdetails.find({"name": data['name'], "password": data['password']})

    if cursor.count() > 0:
        return "true"
    else:
        return "false"

@app.route('/registerUser', methods=['POST'])
def register_user():
    print("Register user")

    coll = db.users
    data = json.loads(request.data.decode('utf-8'))

    result = db.userdetails.insert_one(
        {
            "name" : data['name'],
            "password" : data['password'],
            "email" : data['email'],
            "address" : data['address'],
            "city" : data['city']
        }
    )
    print("succesful add")
    print(result.inserted_id)
    if result.inserted_id != "":
        return "success"
    else:
        return "failure"



if __name__ == '__main__':
    app.run(debug=True)
    
