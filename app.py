from flask import Flask, url_for, request, redirect, session, g, jsonify
from flask.templating import render_template
from database import get_database
from werkzeug.security import generate_password_hash, check_password_hash

from sklearn.tree import DecisionTreeRegressor, export_text
from sklearn.model_selection import train_test_split
import pydotplus
from sklearn.tree import export_graphviz
from io import StringIO
import numpy as np
import re

import os 
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.teardown_appcontext
def close_database(error):
    if hasattr(g, 'viticulture_db'):
        g.viticulture_db.close()

def get_current_user():
    user = None
    if 'user' in session:
        user = session['user']
        db = get_database()
        user_cur = db.execute('select * from users where name = ?', [user])
        user = user_cur.fetchone()
    return user


@app.route('/stats')
def stats():
    db = get_database()
    user = get_current_user()

    op_cur = db.execute('SELECT start_date, duration FROM operations')
    regression_data = op_cur.fetchall()
    start_dates = [row['start_date'] for row in regression_data]
    durations = [float(re.sub('[^0-9.]', '', row['duration'])) for row in regression_data]
    # Convert start_dates to numerical values for the sake of the example
    numerical_start_dates = [i for i in range(len(start_dates))]
    # Reshape data for scikit-learn
    X = np.array(numerical_start_dates).reshape(-1, 1)
    y = np.array(durations)
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    # Train a decision tree regressor
    regressor = DecisionTreeRegressor()
    regressor.fit(X_train, y_train)
    # Visualize the decision tree
    dot_data = StringIO()
    export_graphviz(regressor, out_file=dot_data, filled=True, rounded=True, special_characters=True)
    graph = pydotplus.graph_from_dot_data(dot_data.getvalue())
    graph.write_png("static/decision_tree_regression.png")


    op_cur = db.execute('SELECT operationType, COUNT(*) as count FROM operations GROUP BY operationType')
    classification_data = op_cur.fetchall()
    labels = [row['operationType'] for row in classification_data]
    counts = [row['count'] for row in classification_data]

    op_cur = db.execute('SELECT start_date, duration FROM operations')
    regression_data = op_cur.fetchall()
    start_dates = [row['start_date'] for row in regression_data]
    durations = [row['duration'] for row in regression_data]

    op_cur = db.execute('SELECT operationType, DATE(start_date) as day, COUNT(*) as count FROM operations GROUP BY operationType, day')
    classification_data = op_cur.fetchall()
    operation_types = list(set(row['operationType'] for row in classification_data))
    days = list(set(row['day'] for row in classification_data))
    countss = {op_type: {day: 0 for day in days} for op_type in operation_types}

    for row in classification_data:
        countss[row['operationType']][row['day']] = row['count']


    return render_template('stats.html', user = user , labels=labels, counts=counts, start_dates=start_dates, durations=durations, operation_types=operation_types, days=days, countss=countss)

@app.route('/')
def index():
    user = get_current_user()
    return render_template('home.html', user = user)

@app.route('/login', methods = ["POST", "GET"])
def login():
    user = get_current_user()
    error = None
    db = get_database()
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user_cursor = db.execute('select * from users where name = ?', [name])
        user = user_cursor.fetchone()

        if user:
            if check_password_hash(user['password'], password):
                session['user'] = user['name']
                return redirect(url_for('employees'))
            else:
                error = "Username or Password did not match, try again."
        else:
            error = "Username or Password did not match, try again."

    return render_template('login.html', loginerror = error, user = user)

@app.route('/register', methods=["POST", "GET"])
def register():
    user = get_current_user()
    db = get_database()
    if request.method == 'POST':
        name = request.form['name']
        hashed_password = generate_password_hash(request.form['password'])

        dbuser_cur = db.execute('select * from users where name = ?', [name])
        existing_user = dbuser_cur.fetchone()
        if existing_user:
            return render_template('register.html', registererror = 'Username already taken, try different username.')

        db.execute('insert into users (name, password) values (?, ?)', [name, hashed_password])
        
        db.commit()

        return redirect(url_for('index'))
    return render_template('register.html', user = user)

@app.route('/employees')
def employees():
    user = get_current_user()
    db = get_database()
    emp_cur = db.execute('select * from employees')
    allemp = emp_cur.fetchall()
    return render_template('_employees.html', user= user, allemp= allemp)

@app.route('/addnewemployee', methods=["POST", "GET"])
def addnewemployee():
    user = get_current_user()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        db = get_database()
        db.execute('insert into employees (name, email, phone, address) values (?, ?, ?, ?)', [name, email, phone, address])
        db.commit()
        return redirect(url_for('employees'))
    return render_template('_addnewemployee.html', user = user)

@app.route('/singleemployee/<int:empid>')
def singleemployee(empid):
    user = get_current_user()
    db = get_database()
    emp_cur = db.execute('select * from employees where employeeId = ?', [empid])
    single_emp = emp_cur.fetchone()
    return render_template('_singleemployee.html', user = user, single_emp = single_emp)

@app.route('/fetchoneemp/<int:empid>')
def fetchoneemp(empid):
    user = get_current_user()
    db = get_database()
    emp_cur = db.execute('select * from employees where employeeId = ?', [empid])
    single_emp = emp_cur.fetchone()
    return render_template('_updateemployee.html', user = user, single_emp = single_emp)

@app.route('/updateemployee', methods = ["GET", "POST"])
def updateemployee():
    user = get_current_user()
    if request.method == 'POST':
        empid = request.form['empid']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        db = get_database()
        db.execute('UPDATE employees SET name = ?, email = ?, phone = ?, address = ? WHERE employeeId = ?', [name, email, phone, address, empid])
        db.commit()
        return redirect(url_for('employees'))

    return render_template('_updateemployee.html', user = user)

@app.route('/deleteemp/<int:empid>', methods=["GET", "POST"])
def deleteemp(empid): 
    user = get_current_user()
    if request.method == 'GET':
        db = get_database()
        db.execute('delete from employees where employeeId = ?', [empid])
        db.commit()
        return redirect(url_for('employees'))
    return render_template('_employees.html', user = user)

@app.route('/logout')
def logout():
    session.pop('user', None)
    render_template('home.html')

@app.route('/operations')
def operations():
    user = get_current_user()
    db = get_database()
    op_cur = db.execute('select * from operations')
    allop = op_cur.fetchall()
    return render_template('_operations.html', user= user, allop= allop)

@app.route('/addnewoperation', methods=["POST", "GET"])
def addnewoperation():
    user = get_current_user()
    db = get_database()
    if request.method == 'POST':
        name = request.form['name']
        duration = request.form['duration']
        employeeName = request.form['employeeName']
        operationType = request.form['operationType']
        db.execute('insert into operations (name, duration, employeeName, operationType) values (?, ?, ?, ?)', [name, duration, employeeName, operationType])
        db.commit()
        return redirect(url_for('operations'))
    # Fetch the list of employees
    op_cur = db.execute('SELECT * FROM employees')
    all_emp = op_cur.fetchall()
    return render_template('_addnewoperation.html', user = user, all_emp = all_emp)

@app.route('/singleoperation/<int:opid>')
def singleoperation(opid):
    user = get_current_user()
    db = get_database()
    op_cur = db.execute('select * from operations where operationId = ?', [opid])
    single_op = op_cur.fetchone()
    return render_template('_singleoperation.html', user = user, single_op = single_op)

@app.route('/fetchoneop/<int:opid>')
def fetchoneop(opid):
    user = get_current_user()
    db = get_database()
    op_cur = db.execute('select * from operations where operationId = ?', [opid])
    single_op = op_cur.fetchone()
    return render_template('_updateoperation.html', user = user, single_op = single_op)

@app.route('/updateoperation', methods = ["GET", "POST"])
def updateoperation():
    user = get_current_user()
    if request.method == 'POST':
        opid = request.form['opid']
        name = request.form['name']
        duration = request.form['duration']
        employeeName = request.form['employeeName']
        operationType = request.form['operationType']
        db = get_database()
        db.execute('UPDATE operations SET name = ?, duration = ?, employeeName = ?, operationType = ? WHERE operationId = ?', [name, duration, employeeName, operationType, opid])
        db.commit()
        return redirect(url_for('operations'))
    # Fetch the list of employees
    op_cur = db.execute('SELECT * FROM employees')
    all_emp = op_cur.fetchall()
    return render_template('_updateoperation.html', user = user, all_emp= all_emp)

@app.route('/deleteop/<int:opid>', methods=["GET", "POST"])
def deleteop(opid): 
    user = get_current_user()
    if request.method == 'GET':
        db = get_database()
        db.execute('delete from operations where operationId = ?', [opid])
        db.commit()
        return redirect(url_for('operations'))
    return render_template('_operations.html', user = user)


if __name__ == '__main__':
    app.run(debug = True)