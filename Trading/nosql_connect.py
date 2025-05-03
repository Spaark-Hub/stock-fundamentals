from pymongo.mongo_client import MongoClient

MONGODB_URI = "mongodb+srv://cis5500project:DUxjOob01RFoEjaJ@projectdb.vhf1lti.mongodb.net/?retryWrites=true&w=majority"


client = MongoClient(MONGODB_URI)
database = client["projectdb"]
collection = database["userDetails"]


def insert_record(data):
    print(data)
    email_id = data["email"]
    username = data["username"]
    firstname = data["firstname"]
    lastname = data["lastname"]

    print("EMAIL:", email_id)
    email_check = collection.find_one({"email": email_id})
    print("EMAIL CHECK:", email_check)
    user_check = collection.find_one({"username": username})
    print("USER CHECK:", user_check)
    if email_check == None or user_check == None:
        collection.insert_one(data)
        return True
    else:
        return False


def get_record_details(data):
    username = data["username"]
    print("User:", username)
    fetched_data = collection.find_one({"username": username})
    if fetched_data == None:
        return False
    else:
        return fetched_data
