"""Project Summary
===================

Goal 1: Implementation of a Flask web application using Python3.7,
    flask_wtf, flask_mail,  flask_sqlalchemy,
    flask_rest_jsonapi, flask_bootstrap and wtforms.
Goal 2: Successful implementation of flask json-api for easy interation with
    database data.
Goal 2: Two implemented function that can send email to all registerd users or
    to a selected number of users based on a list of ISBN(s).
Goal 4. Users can edit, add, modify or delete their books. New users can
    also sign up.
Goals 5: Entries in the dashboard can be searched with either the entire Name
    substring of the book or author.

To use the application, a User will only need to register and login.
The rest is very straightforward, and user friendly.

#############################################################################

To send emails to all registered emails by searching through all the ISBN in the
database, the 'Mail All ISBN' button from the dashboard is used. This would
also required further security and access.
To mail Users based only on a list of selected ISBNs, the 'Mail select ISBN'
button is used. This will redirect to a new page where the list of desired
ISBNs can be provided.

The 'Add a Book' button does what it says, just like the 'Search Books' button.
To search a book from a User's dashboard, the user can use The Book Name,
the name of the Author or the ISBN of a book. To search using the name of a book
or the name of an Author, the user could also use a SUBSTRING of these.

The JSON-API is also available from www.site.com/books for example.
This Json-api can also be sorted, depending on the desired result.

###This single 'app.py' is the main and only available script for this project.###

Technologies
=================
Python3.7
Flask (and its related/required libraries)
wtforms
werkzeug

MODELS
==========

A very basic database was created using sqlalchemy. The books from all users
are stored in this database, but NO user can have access or delete, or modify
the entries of another user.
Other Classes includes:
1.  	A data abstraction layer (Schema model) for api access to the base model which
    possibility to view all books or search for a given book.

Miscelaneous
=============
Subfolders in the application
-----------------------------
static: static files
templates: Templates folder
env: The virtual environment
_build/html/index.html : A documentation web page (see also code.html,project.html)
*.rst: documentation files

app.py : main and only project file.
"""
############### IMPORT NECESSARY MODELS #######################################
from flask import Flask, render_template, redirect, url_for,request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, \
                        logout_user, current_user
from sqlalchemy import literal
###################################

from flask import jsonify
from flask_mail import Mail, Message
import os
import json

from marshmallow_jsonapi.flask import Schema
from marshmallow_jsonapi import fields
from flask_rest_jsonapi import Api, ResourceDetail, ResourceList
################################################################################

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobeasecretkey!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL','sqlite:////home/tony/project/database.db')
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

##################################################################
app.config['MAIL_SERVER']='SMTP.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'email@mail.com'
app.config['MAIL_PASSWORD'] = 'password'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)
###################################################################
######################## MODELS ###################################
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(80))

class Books(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    name = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return '<Books model {}>'.format(self.id)

db.create_all()

# Create data abstraction layer
class BookSchema(Schema):
    class Meta:
        type_ = 'books'
        self_view = 'book_one'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'book_all'

    id = fields.Integer()
    name = fields.Str(required=True)
    author = fields.Integer(load_only=True)
    isbn = fields.Str()
    email = fields.Str()


class BookAll(ResourceList):
    schema = BookSchema
    data_layer = {'session': db.session,
                  'model': Books}

class BookOne(ResourceDetail):
    schema = BookSchema
    data_layer = {'session': db.session,
                  'model': Books}

api = Api(app)
api.route(BookAll, 'book_all', '/books')
api.route(BookOne, 'book_one', '/books/<int:id>')

################################################################################
############################# VIEWS  ###########################################

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=5, max=50)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), \
                            Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=5, max=50)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


# index view, before login with options for login, signup
@app.route('/')
def index():
    return render_template('index.html')

# login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))

        return '<h1>Invalid username or password</h1>'

    return render_template('login.html', form=form)


#signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New user has been created! Login Now!</h1>'
    return render_template('signup.html', form=form)


#dashboard for logged in user
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        book = Books.query.filter_by(email=current_user.email).all()
        try:
            db.session.add(book)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding your book'
    else:
        books = Books.query.filter_by(email=current_user.email).all()
        return render_template('dashboard.html', books=books, \
                name=current_user.username)

#view for the addition of a book
@app.route('/add_book', methods=['POST', 'GET'])
@login_required
def add_book():
    if request.method == 'POST':
        books = Books(name=request.form['name'], author = request.form['author'],
                    isbn=request.form['isbn'], email = current_user.email)
        try:
            db.session.add(books)
            db.session.commit()
            return redirect('dashboard')
        except:
            return 'There was an issue adding your book!'
    else:
        return render_template('add_book.html')


#to delete an entry in the database
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    book_to_delete = Books.query.get_or_404(id)
    try:
        db.session.delete(book_to_delete)
        db.session.commit()
        return redirect('/dashboard')
    except:
        return 'There was a problem deleting that book!'


#to update an entry in the database
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    book = Books.query.get_or_404(id)
    if request.method == 'POST':
        oldId = request.form.get("oldId")
        book = Books.query.filter_by(id=oldId).first()
        book.name = request.form['name']
        book.author = request.form['author']
        book.isbn = request.form['isbn']
        try:
            db.session.commit()
            return redirect('/dashboard')
        except:
            return 'There was an issue updating your book!'
    else:
        return render_template('update.html', book=book)


#view for searching through the books in the database
@app.route('/search', methods=['POST','GET'])
@login_required
def search():
    if request.method == 'POST':
        if request.form.get('name'):
            _name = request.form.get("name")
            books = Books.query.filter(Books.name.contains(_name)).filter_by(email=current_user.email).all()
            return render_template('results.html',books=books)
        elif request.form.get('author'):
            _author = request.form.get("author")
            books = Books.query.filter(Books.author.contains(_author)).filter_by(email=current_user.email).all()
            return render_template('results.html',books=books)
        elif request.form.get('isbn'):
            _isbn = request.form.get("isbn")
            books = Books.query.filter_by(isbn=_isbn,email=current_user.email).all()
            return render_template('results.html',books=books)
        else:
            return render_template('search.html')
    else:
        return render_template('search.html')


#search results
@app.route('/results', methods=['GET','POST'])
@login_required
def results():
    if request.method == 'POST':
        if request.form.get('name'):
            books = Books.query.order_by(Books.name).all()
        elif request.form.get('author'):
            books = Books.query.order_by(Books.author).all()
        else:
            books = Books.query.order_by(Books.isbn).all()
        books = Books.query
    return render_template('results.html', books=books)


#logout view
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/isbn_list', methods=['POST','GET'])
@login_required
def get_select_ISBN():
    """ A function that, given certain ISBN/s numbers, queries the database
     for each of the entries and returns the emails of any found entry.
     Emails are then sent to those emails if found.
     For this function, the possibility to search for 4 ISBNs was made available.
     This can be enhanced by getting the entire ISBN as a comma-seperated input
     from the user from the front end.
     The 4 inputs from the user are firsts checked if they are empty, then their
     corresponding emails is extracted from the database.
     Each of the reciepients is then forwarded an email.
    """
    if request.method == 'POST':
        isbn1, isbn2, isbn3, isbn4 = request.form['isbn1'], request.form['isbn2']\
                        , request.form['isbn3'], request.form['isbn4']

        isbn_list = [isbn1, isbn2, isbn3, isbn4]
        _email = [] #empty list to hold emails corresponding to ISBN list
        #recieved by the function
        for i in isbn_list:
            if i:
                try:
                    _email.append(Books.query.filter_by(isbn=i).first().email)
                    #appending to the empty email list
                except:
                    return ('No record found for the ISBN %s' %i)
        #end for
        if len(_email) == 0: # When no record is found, do nothing.
            return ('Entries non existent in database.')
        else:
            unique_emails = unique_list(_email)
            if len(unique_emails) == 1: # when just one email for all present ISBN
                #value = Books.query.filter_by(email=unique_emails).all()
                value = Books.query.filter(Books.email==unique_emails[0])
                # value is a Book object containing dabase entries
                mail_content = []
                res = []  # list for holding individual data from database
                for i in value:
                    res.append([i.isbn, i.author, i.name])
                for i in range(len(res)):
                    mail_content.append({
                        'Book': res[i][2],
                        'author': res[i][1],
                        'ISBN': res[i][0]
                    })
                try:
                    with app.app_context(): # sending email with app context
                        msg = Message(subject = "Hello",
                                      sender = app.config.get("MAIL_USERNAME"),
                                      recipients = [unique_emails[0]],
                                      html = json.dumps(mail_content[:]))
                        mail.send(msg)
                    return render_template('success.html')
                except:
                    return ('Message to %s could not be sent!' %unique_emails[0])
            else:
                for unique_email in unique_emails:
                    value = Books.query.filter_by(email=unique_email).all()
                    #querrying for individual email found.
                    mail_content = []
                    res = []
                    for i in value:
                        res.append([i.isbn, i.author, i.name])
                    for i in range(len(res)):
                        mail_content.append({
                            'Book': res[i][2],
                            'author': res[i][1],
                            'ISBN': res[i][0]
                        })
                    try:
                        with app.app_context(): # sending email with app context
                            msg = Message(subject = "Hello",
                                          sender = app.config.get("MAIL_USERNAME"),
                                          recipients = [unique_email],
                                          html = json.dumps(mail_content[:]))
                            mail.send(msg)
                        return render_template('success.html')
                    except:
                        return ('Message to %s could not be sent!' %unique_email)
    else:
        return render_template('isbn_list.html')


@app.route('/all_isbn', methods=['POST','GET'])
@login_required
def get_all_ISBN():
    """A function to return a list containing the ISBN numbers of
    all available book entries in the database.
    First the entire database is querried for all available books. These ISBNs
    are sorted according the registered user emails.
    They are then forwared emails with the book name, book author and ISBN of the
    books in the database.
    """
    if request.method == 'GET':
        res = [] # empty list to contain database querries
        try:
            value = Books.query.all()
            if len(value) == 1:
                res.append([value.email, value.isbn, value.author, value.name])
                email = [(res[0][0])] #To get all emails (one actually)
                mail_content = []
                mail_content.append(
                    {
                        'Book': res[0][3],
                        'author': res[0][2],
                        'ISBN': res[0][1]
                    }
                )
                try:
                    with app.app_context(): # sending email with app context
                        msg = Message(subject = "Hello",
                                      sender = app.config.get("MAIL_USERNAME"),
                                      recipients = [email],
                                      html = json.dumps(mail_content[:]))
                        mail.send(msg)
                    return render_template('success.html')
                except:
                    return ('Message to %s could not be sent!' %email)

            elif len(value) > 1:
                for i in value:
                    res.append([i.email, i.isbn, i.author, i.name])
                emails = [(res[i][0]) for i in range(len(res))]
                unique_emails = unique_list(emails) #sorting available Emails
                #in the database
                for unique_email in unique_emails: #looping through all the
                #unique emails and extracting all data related to them in the
                #database
                    mail_content = [] # container for all entries of a given email
                    for _it, email in enumerate(emails):
                        if email == unique_email:
                            mail_content.append(
                                {
                                    'Book': res[_it][3],
                                    'author': res[_it][2],
                                    'ISBN': res[_it][1]
                                }
                            )
                    try:
                        with app.app_context():
                            msg = Message(subject="Hello",
                                          sender=app.config.get("MAIL_USERNAME"),
                                          recipients=[unique_email],
                                          html= json.dumps(mail_content[:]))
                            mail.send(msg)
                        return render_template('success.html')
                    except:
                        return ('Message to %s could not be Sent!' %unique_email)
                return
        except:
            return ('Database is empty!')
        return
    else:
        return


def unique_list(input_list):
    """ A python function to sort the entries in the database and extract
    only unique entries so that every entry in the database associated to
    such email can be correctly associated to it.
    """
    output_list = []
    for word in input_list:
        if word not in output_list:
            output_list.append(word)
    return output_list

def _list(aa):
    cou = []
    for count,ele in enumerate(aa):
        if ele == '':
            cou.append(count)
    if len(cou) == 0:
        word = "".join(aa)
    else:
        word = [None]*(len(cou)+1)
        word[0] = "".join(aa[:cou[0]])
        word[-1] = "".join(aa[cou[-1]+1:])
        for i in range(1,len(cou)):
            word[i] = "".join(aa[cou[i-1]:cou[i]])
    return word

############################################
#initialization
if __name__ == '__main__':
    #app.run()
    app.run(debug=True)
