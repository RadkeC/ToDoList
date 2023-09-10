from pymongo import MongoClient

from config import env


def get_database():
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = env('CONNECTION_STRING')

    # Create a connection using MongoClient.
    client = MongoClient(CONNECTION_STRING)

    # Create and return db
    return client['ToDoList']
