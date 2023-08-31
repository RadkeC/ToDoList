from threading import Thread
import time
from flask import Flask, flash, request, render_template, redirect
from flask_apscheduler import APScheduler

from database import get_database
from kafka import produce, consume_users, consume_tasks
from config import env

app = Flask(__name__)
#app.secret_key = 'ajsdbfhbsdhugfubdijfbSIDJgfbzlsdibg'
app.secret_key = env('SECRET_KEY')
scheduler = APScheduler()

collection_users = get_database()['Users']
collection_tasks = get_database()['Tasks']


@app.route('/test', methods=['GET', 'POST'])
def test_page():
    return "Test page"


@app.route('/', methods=['GET', 'POST'])
def main_page():
    if 'user' in request.cookies:
        user = request.cookies['user']
        if request.method == 'POST':
            print(request.form.keys())
            if 'logout_button' in request.form.keys():
                response = redirect('/')
                response.set_cookie('user', expires=0)
                return response
            elif 'delete_user_button' in request.form.keys():
                # userdata = collection_users.find_one({'username': user})
                produce(topic='ToDoList_Users', key='delete_user', value={'username': user})
                produce(topic='ToDoList_Tasks', key='delete_user_tasks', value={'user': user})
                response = redirect('/')
                response.set_cookie('user', expires=0)
                return response
            elif 'done_task_button' in request.form.keys():
                produce(topic='ToDoList_Tasks', key='done_task', value={'_id': request.form['done_task_button']})
            elif 'undone_task_button' in request.form.keys():
                produce(topic='ToDoList_Tasks', key='undone_task', value={'_id': request.form['undone_task_button']})
            elif 'add_task_button' in request.form.keys():
                produce(topic='ToDoList_Tasks', key='add_task',
                        value={'user': user, 'task': request.form['task_text'], 'done': False})
            elif 'delete_task_button' in request.form.keys():
                produce(topic='ToDoList_Tasks', key='delete_task',
                        value={'_id': request.form['delete_task_button']})

            time.sleep(0.1)
        content = {'user': user, 'tasks': collection_tasks.find({'user': user})}
        return render_template('main_page.html', content=content)
    else:
        # LOGIN CASE
        if request.method == 'POST':
            if 'login_button' in request.form.keys():
                userdata = collection_users.find_one({'username': request.form['username']})
                if userdata:
                    if userdata['password'] == request.form['password']:
                        response = redirect('/')
                        response.set_cookie('user', userdata['username'])
                        return response
                flash('Invalid credentials.')
                return render_template('main_page.html', content={})
            elif 'register_page_button' in request.form.keys():
                return redirect('/add_user')
            else:
                return render_template('main_page.html', content={})
        else:
            return render_template('main_page.html', content={})


@app.route('/add_user', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register_page.html')
    elif request.method == 'POST':
        if collection_users.find_one({'username': request.form['username']}):
            flash('Username is alerady taken. Please choose another.')
            return render_template('register_page.html')
        else:
            produce(topic='ToDoList_Users', key='add_user',
                    value={'username': request.form['username'], 'password': request.form['password']})
            # response = make_response(redirect('/'))
            response = redirect('/')
            response.set_cookie('user', request.form['username'])
            return response


if __name__ == '__main__':
    #bt_consume_tasks = Thread(target=consume_tasks)
    #bt_consume_tasks.start()

    #bt_consume_users = Thread(target=consume_users)
    #bt_consume_users.start()

    scheduler.add_job(id='consume_tasks', func=consume_tasks)
    scheduler.add_job(id='consume_users', func=consume_users)
    scheduler.start()

    app.run(debug=True)#, use_reloader=False)
    # p.join()
