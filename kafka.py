from confluent_kafka import Producer, Consumer
from json import loads, dumps
from time import sleep
from bson.objectid import ObjectId

from database import get_database
from config import env



# Creating delivery callback for producer
def delivery_callback(err, msg):
    if err:
        print('ERROR: Message failed delivery: {}'.format(err))
    else:
        print("Produced event to topic '{topic}': key = '{key:12}' value = '{value:12}'".format(
            topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))


# Create producer function to send messages to broker in choosen topic
def produce(topic, key, value):
    # Config
    text_config = {
        #'bootstrap.servers': 'localhost:29092'
        'bootstrap.servers': env('CLOUDKARAFKA_HOSTNAME'),
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "SCRAM-SHA-256",
        "sasl.username": env('CLOUDKARAFKA_USERNAME'),
        "sasl.password": env('CLOUDKARAFKA_PASSWORD')
    }

    # Create Producer instance
    producer = Producer(text_config)

    # Produce message
    producer.produce(topic=env('PREFIX') + topic, key=key, value=dumps(value), callback=delivery_callback)

    # Block until the messages are sent.
    producer.flush()


# Consumer function for Users -> for background task
def consume_users(topic=env('PREFIX') + 'ToDoList_Users'):
    print('Initialized Users background task')
    # Initialize topic
    produce(topic, 'topic_initialization', '')
    # Get connection to Users table in database
    collection_users = get_database()['Users']

    # Config
    text_config = {
        #'bootstrap.servers': 'localhost:29092',
        'bootstrap.servers': env('CLOUDKARAFKA_HOSTNAME'),
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "SCRAM-SHA-256",
        "sasl.username": env('CLOUDKARAFKA_USERNAME'),
        "sasl.password": env('CLOUDKARAFKA_PASSWORD'),
        'group.id': env('PREFIX') + 'python_group_1',
        'auto.offset.reset': 'earliest'
    }

    # Create Consumer instance
    consumer = Consumer(text_config)

    # Subscribe to topic
    consumer.subscribe([topic])

    while True:
        # Poll for new messages from Kafka and procced them
        try:
            waiting_flag = True
            while True:
                # Wait for new message
                msg = consumer.poll(0.1)

                # No new messages
                if msg is None:
                    if waiting_flag:
                        print("Consumer_users is waiting...")
                        waiting_flag = False
                # Message error
                elif msg.error():
                    waiting_flag = True
                    print("ERROR: %s".format(msg.error()))
                # New message
                else:
                    waiting_flag = True
                    # Extract the key and value
                    key = msg.key().decode('utf-8')
                    value = loads(msg.value().decode('utf-8'))
                    print('Consumer: ', key, value)

                    # Add user case
                    if key == 'add_user':
                        collection_users.insert_one(value)
                    # Edit user case
                    elif key == 'edit_user':
                        old_user = {"_id": value['old_user']}
                        new_user = {"$set": {value['new_user']}}
                        collection_users.update_one(old_user, new_user)
                    # Delete user case
                    elif key == 'delete_user':
                        collection_users.delete_one(value)
                    # Unexpected case
                    else:
                        print('Unknow key: {}'.format(key))
        # In case of error recreate consumer isntance
        except:
            # Create Consumer instance
            consumer = Consumer(text_config)
            # Subscribe to topic
            consumer.subscribe([topic])

        finally:
            sleep(5)
            # Leave group and commit final offsets
            print('Consumer_tasks in ending ...')
            consumer.close()


def consume_tasks(topic=env('PREFIX') + 'ToDoList_Tasks'):
    print('Initialized Tasks background task')
    # Initialize topic
    produce(topic, 'topic_initialization', '')
    # Get connection to Users table in database
    collection_tasks = get_database()['Tasks']

    # Tekst config
    text_config = {
        #'bootstrap.servers': 'localhost:29092',
        'bootstrap.servers': env('CLOUDKARAFKA_HOSTNAME'),
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "SCRAM-SHA-256",
        "sasl.username": env('CLOUDKARAFKA_USERNAME'),
        "sasl.password": env('CLOUDKARAFKA_PASSWORD'),
        'group.id': env('PREFIX') + 'python_group_1',
        'auto.offset.reset': 'earliest'
    }

    # Create Consumer instance
    consumer = Consumer(text_config)

    # Subscribe to topic
    consumer.subscribe([topic])

    while True:
        # Poll for new messages from Kafka and print them.
        try:
            waiting_flag = True
            while True:
                msg = consumer.poll(0.1)

                if msg is None:
                    # Initial message consumption may take up to
                    # `session.timeout.ms` for the consumer group to
                    # rebalance and start consuming
                    if waiting_flag:
                        print("Consumer_tasks is waiting...")
                        waiting_flag = False
                elif msg.error():
                    waiting_flag = True
                    print("ERROR: %s".format(msg.error()))
                else:
                    waiting_flag = True
                    key = msg.key().decode('utf-8')
                    value = loads(msg.value().decode('utf-8'))
                    if '_id' in value:
                        value['_id'] = ObjectId(value['_id'])

                    # Extract the (optional) key and value, and print.
                    print('Consumer: ', key, value)
                    if key == 'add_task':
                        collection_tasks.insert_one(value)
                    elif key == 'done_task':
                        task = {"_id": value['_id']}
                        new_value = {"$set": {'done': True}}
                        collection_tasks.update_one(task, new_value)
                    elif key == 'undone_task':
                        task = {"_id": value['_id']}
                        new_value = {"$set": {'done': False}}
                        collection_tasks.update_one(task, new_value)
                    elif key == 'delete_task':
                        collection_tasks.delete_one(value)
                    elif key == 'delete_user_tasks':
                        collection_tasks.delete_many(value)
                    else:
                        print('Unknow key: {}'.format(key))

        except:
            # Create Consumer instance
            consumer = Consumer(text_config)
            # Subscribe to topic
            consumer.subscribe([topic])
        finally:
            # Leave group and commit final offsets
            sleep(5)
            print('Consumer_users in ending ...')
            consumer.close()


if __name__ == '__main__':
    consume_tasks()
    #produce('ToDoList_Task', 'a', 'a')
