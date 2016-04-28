#!flask/bin/python
from flask import Flask, jsonify, request, make_response
from flask.ext.cors import CORS
import pymongo 
import json 
import re
import datetime
import string
import random
from pymongo import MongoClient
from bson import BSON
from bson import json_util
from recommendations import getRecommendations

connection = MongoClient("mongodb://localhost:27017")
db = connection.recommender 
reviews = db.reviews
users = db.users
user_ratings = db.user_ratings

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
    restaurants = reviews.find({"user_id": user_id}).sort([("date", -1)])
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

@app.route('/getCities', methods=['POST'])
def get_cities():
    data = []
    cities = []
    with open('cities.txt') as f:
        cities = f.read().splitlines() 
        for c in cities:
            city = {}
            city["name"] = c
            data.append(city)
    resp = make_response(json.dumps(list(data), sort_keys=True, indent=4, default=json_util.default))
    return resp

@app.route('/mostPopularCategoriesByCity', methods=['POST'])
def get_most_popular_by_city():
    restaurants = db.businesses
    data = json.loads(request.data)
    cities = {}
    for r in restaurants.find():
        if r["city"] == data["city"]: 
            if r["city"] not in cities:
                cities[r["city"]] = {}

            if "Food" in r["categories"] or "Restaurants" in r["categories"]:
                for category in r["categories"]:
                    if category not in cities[r["city"]]:
                        cities[r["city"]][category] = 0
                    cities[r["city"]][category] = cities[r["city"]][category] + 1

    resp = make_response(json.dumps(cities, sort_keys=True, indent=4, default=json_util.default))
    return resp

#services for registering users
@app.route('/authenticateUser', methods=['POST'])
def authenticate_user():
    print("Service has been called")
    data = json.loads(request.data.decode('utf-8'))
    cursor = users.find({"name": data['name'], "password": data['password']})
    if cursor.count() > 0:
        for c in cursor:
            resp = make_response(json.dumps(["true", c['user_id']]))
            return resp
    else:
        resp = make_response(json.dumps(["false", 0]))
        return resp

@app.route('/registerUser', methods=['POST'])
def register_user():
    print("Register user")
    data = json.loads(request.data.decode('utf-8'))
    user_id = id_generator()
    result = users.insert_one(
        {
            "user_id": user_id,
            "name" : data['name'],
            "password" : data['password'],
            "email" : data['email'],
            "address" : data['address']
        }
    )

    user_ratings.insert( {"_id": user_id, user_id: {}})
    print("succesful add")
    print(result.inserted_id)
    if result.inserted_id != "":
        return "success"
    else:
        return "failure"


def id_generator(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

if __name__ == '__main__':
    app.run(debug=True)
    
