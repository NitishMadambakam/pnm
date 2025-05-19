from flask import Flask, redirect, url_for, request, render_template, flash,session
import pymysql
from pymysql.err import IntegrityError
from flask_session import Session
from key import secret_key, salt
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import sendmail

app = Flask(__name__)
app.secret_key = secret_key
app.config['SESSION_TYPE'] = 'filesystem'

mdb = pymysql.connect(
    host="localhost",
    user="root",
    password="admin",
    db="users",
    cursorclass=pymysql.cursors.DictCursor
)

@app.route('/')
def index():
    return render_template('title.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor=mdb.cursor()
        cursor.execute('SELECT count(*) from pnm where username=%s and password=%s',[username,password])
        count = list(cursor.fetchone().values())[0]
        if count == 1:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            flash("Invalid Username or Password")
            return render_template('login.html')
    return render_template('login.html')

@app.route('/homepage')
def home():
    if session.get('user'):
        return render_template('homepage.html')
    else:
        return redirect(url_for('login'))

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mdb.cursor()
        cursor.execute('select count(*) from pnm where username=%s', [username])
        count = list(cursor.fetchone().values())[0]
        cursor.execute('select count(*) from pnm where email=%s', [email])
        count1 = list(cursor.fetchone().values())[0]
        cursor.close()
        if count == 1:
            flash("Username already in use")
            return render_template('registration.html')
        elif count1 == 1:
            flash("Email already in use")
            return render_template('registration.html')
        data = {'username': username, 'password': password, 'email': email}
        subject = 'Email Confirmation'
        body = f"Thanks for signing up\n\nFollow this link for further steps - {url_for('confirm', token=token(data), _external=True)}"
        sendmail(to=email, subject=subject, body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer = URLSafeTimedSerializer(secret_key)
        data = serializer.loads(token, salt=salt, max_age=180)
    except Exception as e:
        return 'Link expired, register again'
    else:
        cursor = mdb.cursor()
        email = data['email']
        cursor.execute('select count(*) from pnm where username=%s', [data['username']])
        count = list(cursor.fetchone().values())[0]
        if count == 1:
            cursor.close()
            flash("You are already registered")
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into pnm values(%s,%s,%s)', [data['username'], data['password'], data['email']])
            mdb.commit()
            cursor.close()
            flash("Details registered")
            return redirect(url_for('login'))

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash("Successfully Loggedout")
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
    
@app.route('/addnotes', methods = ['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            username = session.get('user')
            cursor = mdb.cursor()
            cursor.execute('insert into notes (title, content, added_by) values(%s,%s,%s)',[title,content,username])
            mdb.commit()
            cursor.close()
            flash('Notes added successfully')
            return redirect(url_for('allnotes'))
        return render_template('addnotes.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/allnotes')
def allnotes():
    if session.get('user'):
        username = session.get('user')
        cursor = mdb.cursor()
        cursor.execute('select nid, title, date from notes where added_by = %s order by date desc',[username])
        data = list(cursor.fetchall())
        print(data)
        cursor.close()
        return render_template('table.html',data = data)
    else:
        return redirect('login')

@app.route('/viewnotes/<int:nid>')
def viewnotes(nid):
    if session.get('user'):
        cursor = mdb.cursor()
        cursor.execute('select title, content from notes where nid=%s', [nid])
        data = cursor.fetchone()
        cursor.close()
        if data:  # always check if note exists
            return render_template('view.html', title=data['title'], content=data['content'])
        else:
            flash("Note not found")
            return redirect(url_for('allnotes'))
    else:
        return redirect(url_for('login'))

@app.route('/delete/<int:nid>')
def delete(nid):
    if session.get('user'):
        cursor = mdb.cursor()
        cursor.execute('delete from notes where nid = %s',[nid])
        mdb.commit()
        cursor.close()
        flash('Notes deleted')
        return redirect(url_for('allnotes'))
    else:
         return redirect(url_for('login'))
    
@app.route('/updatenotes/<int:nid>', methods=['GET', 'POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor = mdb.cursor()
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            cursor.execute('UPDATE notes SET title=%s, content=%s WHERE nid=%s', [title, content, nid])
            mdb.commit()
            cursor.close()
            flash('Notes updated successfully')
            return redirect(url_for('allnotes'))
        else:
            cursor.execute('SELECT title, content FROM notes WHERE nid=%s', [nid])
            data = cursor.fetchone()
            cursor.close()
            if data:
                return render_template('update.html', title=data['title'], content=data['content'])
            else:
                flash("Note not found")
                return redirect(url_for('allnotes'))
    else:
        return redirect(url_for('login'))

    
app.run(use_reloader=True, debug=True)
