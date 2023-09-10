from threading import Thread
import time
from flask import Flask, flash, request, render_template, redirect
from flask_apscheduler import APScheduler

from database import get_database
from kafka import produce, consume_users, consume_tasks
from config import env

# Create Flask app and background task holder
app = Flask(__name__)
app.secret_key = env('SECRET_KEY')
scheduler = APScheduler()

# Create background tasks with consumer for Users and Tasks
scheduler.add_job(id='consume_tasks', func=consume_tasks)
scheduler.add_job(id='consume_users', func=consume_users)
scheduler.start()

collection_users = get_database()['Users']
collection_tasks = get_database()['Tasks']


# Simple test page
@app.route('/test', methods=['GET', 'POST'])
def test_page():
    return "Test page"


# Main page
@app.route('/', methods=['GET', 'POST'])
def main_page():
    # User is logged option
    if 'user' in request.cookies:
        user = request.cookies['user']
        # Working with data from POST form
        if request.method == 'POST':
            # Logout case
            if 'logout_button' in request.form.keys():
                response = redirect('/')
                response.set_cookie('user', expires=0)
                return response
            # Delete logged user case
            elif 'delete_user_button' in request.form.keys():
                # Delete user from db
                produce(topic='ToDoList_Users', key='delete_user', value={'username': user})
                # Delete user's tasks from db
                produce(topic='ToDoList_Tasks', key='delete_user_tasks', value={'user': user})
                # Redirect to main page and delete cookie
                response = redirect('/')
                response.set_cookie('user', expires=0)
                return response
            # Change task's status to done
            elif 'done_task_button' in request.form.keys():
                produce(topic='ToDoList_Tasks', key='done_task', value={'_id': request.form['done_task_button']})
            # Change task's status to undone
            elif 'undone_task_button' in request.form.keys():
                produce(topic='ToDoList_Tasks', key='undone_task', value={'_id': request.form['undone_task_button']})
            # Add new task
            elif 'add_task_button' in request.form.keys():
                produce(topic='ToDoList_Tasks', key='add_task',
                        value={'user': user, 'task': request.form['task_text'], 'done': False})
            # Delete single task
            elif 'delete_task_button' in request.form.keys():
                produce(topic='ToDoList_Tasks', key='delete_task',
                        value={'_id': request.form['delete_task_button']})
            # Let background consuemer task time to proceed data
            time.sleep(0.1)
        # Create data to render page from template
        content = {'user': user, 'tasks': collection_tasks.find({'user': user})}
        return render_template('main_page.html', content=content)
    # User isn't logged option
    else:
        # Working with data from POST form
        if request.method == 'POST':
            # Login case
            if 'login_button' in request.form.keys():
                # Get user's data from db
                userdata = collection_users.find_one({'username': request.form['username']})
                # Username exists in db
                if userdata:
                    # Confirm password
                    if userdata['password'] == request.form['password']:
                        # Redirect to main page with logged user
                        response = redirect('/')
                        response.set_cookie('user', userdata['username'])
                        return response
                # Wrong user data
                flash('Invalid credentials.')
                return render_template('main_page.html', content={})
            # Register new user case -> redirect
            elif 'register_page_button' in request.form.keys():
                return redirect('/add_user')
            # Unexpected post result in redirect to main page
            else:
                return render_template('main_page.html', content={})
        else:
            return render_template('main_page.html', content={})


# Registe new user page
@app.route('/add_user', methods=['GET', 'POST'])
def register():
    # Render template if get method
    if request.method == 'GET':
        return render_template('register_page.html')
    # If post method try create user
    elif request.method == 'POST':
        # Check if user already exists
        if collection_users.find_one({'username': request.form['username']}):
            flash('Username is alerady taken. Please choose another.')
            return render_template('register_page.html')
        # Create user and log in
        else:
            produce(topic='ToDoList_Users', key='add_user',
                    value={'username': request.form['username'], 'password': request.form['password']})
            response = redirect('/')
            response.set_cookie('user', request.form['username'])
            return response




if __name__ == '__main__':


    app.run(debug=True)
