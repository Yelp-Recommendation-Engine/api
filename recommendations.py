#modules
import re
import random
import numpy as np
import matplotlib.cm as cm
import statsmodels.api as sm
from collections import Counter
from collections import defaultdict
from scipy.stats.stats import pearsonr
import matplotlib.pyplot as plt
from math import sqrt
import time
import json
from scipy import spatial
import time
import pymongo 
from pymongo import MongoClient
from bson import BSON
from bson import json_util

connection = MongoClient("mongodb://localhost:27017")
db = connection.recommender 

# main dataset
user_dict={}
business_dict={}
itemsim = {}
B = {}

def prepareDatasets():
    for user in db.user_ratings.find():
    	user.pop("_id", None) 
    	user_dict.update(user)

    for business in db.business_ratings.find():
    	business.pop("_id", None) 
    	business_dict.update(business)

    for item in db.similarity_matrix.find():
    	item.pop("_id", None) 
    	itemsim.update(item)

    for business in db.businesses.find():
        b_id = business["business_id"]
        B[b_id] = business

    #top rated businesses to be recommended when there is no record
    topRestaurants={}
    for i in business_dict:
        rates=business_dict[i].values()
        mean=np.mean(rates)
        if mean ==5:
            topRestaurants[i]=len(rates)
    topRestaurants = [(score,item) for item,score in topRestaurants.items()]
    topRestaurants.sort()
    topRestaurants.reverse()
    topRestaurants = [(5.0,j) for i,j in topRestaurants[:5]]



    # with open('B.json', 'r') as f:
    #     data = {}
    #     for line in f:
    #         data = json.loads(line)
    #     B = data

def getRecommendedItems(user):
    prepareDatasets()
    itemMatch = itemsim
    prefs = user_dict
    userRatings=prefs[user]
    scores={}
    totalSim={}
    # Loop over items rated by this user
    for (item,rating) in userRatings.items():
             # Loop over items similar to this one
             for arr in itemMatch[item]:
                    # Ignore if this user has already rated this item
                    similarity = arr[0] 
                    item2 = arr[1] 
                    if item2 in userRatings: continue
                    # Weighted sum of rating times similarity
                    scores.setdefault(item2,0)
                    scores[item2]+=similarity*rating
                    # Sum of all the similarities
                    totalSim.setdefault(item2,0)
                    totalSim[item2]+=similarity

    # Divide each total score by total weighting to get an average 
    rankings=[(score/totalSim[item],item) for item,score in scores.items() if score>0]
    
    # Return the rankings from highest to lowest 
    rankings.sort( )
    rankings.reverse( )
    print(len(rankings))
    if rankings:
        return  [(i,B[j]) for i,j in rankings[:20]]
    else:
        return  [(i,B[j]) for i,j in topRestaurants]

def getRecommendations(user_id):
    recItems = getRecommendedItems(user_id) #random.sample(user_dict.keys(),1)[0]
    return recItems