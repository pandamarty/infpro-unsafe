from flask import Flask, render_template, request, redirect, url_for, session, flash
import re
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore 
from flask_security.forms import RegisterForm

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)

# http://localhost:5000/pythonlogin/ - this will be the login page, we need to use both GET and POST requests
@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        #injection code --> " or ""="
        cursor.execute('SELECT * FROM user WHERE username ="' + username + '" AND password ="' + password + '"')
        #safe code
        #cursor.execute('SELECT * FROM user WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in user table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)
    
# http://localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        #inection code --> 105; DROP TABLE Suppliers
        #cursor.execute("SELECT * FROM user WHERE username=" + username)
        #safe code
        cursor.execute('SELECT * FROM user WHERE username = %s', (username))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into user table
            cursor.execute('INSERT INTO user VALUES (NULL, %s, %s,%s, %s)', (username, password, email,1))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

@app.route('/pythonlogin/home', methods=['GET', 'POST'])
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        msg=''
        if request.method == 'POST':
            thread1 = request.form.get('thread')
            
            if (thread1 == ''):
                msg='The question was too short'
            else:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("INSERT INTO thread VALUES (NULL, %s, %s)", [thread1, session['id']])
                mysql.connection.commit()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * from thread")
        data = cursor.fetchall()
        
        return render_template('home.html', username=session['username'], data=data, msg=msg)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
    

@app.route('/pythonlogin/reply/<threadid>', methods=['GET', 'POST'])
def reply(threadid):
    msg=''
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT *  FROM thread, user WHERE thread.id="+threadid+" && user.id=thread.userid")
        data = cursor.fetchall()
        if request.method == 'POST':
            reply = request.form.get('message')
            
            if (reply == ''):
                msg='The answer was too short'
            else:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("INSERT INTO reply VALUES (NULL, %s, %s, %s)", [threadid, session['id'], reply])
                mysql.connection.commit()
        cursor.execute("SELECT * from reply, user WHERE  user.id=reply.user_id && reply.thread_id="+threadid)
        rdata = cursor.fetchall()
        return render_template('thread.html', username=session['username'], data=data, replies=rdata, msg=msg)
    return redirect(url_for('login'))
    
# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/pythonlogin/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/pythonlogin/password', methods=['GET', 'POST'])
def password():
    msg = ''
    if request.method == 'POST' and 'newPW' in request.form and 'confPW' in request.form:
        newPW = request.form['newPW']
        confirmPW = request.form['confPW']
        if newPW == confirmPW:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE user SET password=%s WHERE id = %s', (confirmPW, session['id'],))
            mysql.connection.commit()
            msg = 'You have successfully changed your password!'
        else:
            msg = 'The two password have to match!'
    elif request.method == 'POST':
        msg = 'Please fill out the fields!'
    return render_template('password.html', msg=msg)
    
