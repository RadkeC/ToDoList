from pymongo import MongoClient

from config import env


def get_database():
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    #CONNECTION_STRING = "mongodb+srv://mongouser:pkpmongo@todolist.itm6a3h.mongodb.net/?retryWrites=true&w=majority"
    CONNECTION_STRING = env('CONNECTION_STRING')

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client['ToDoList']
