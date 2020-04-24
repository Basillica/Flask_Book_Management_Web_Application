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
################################################################################

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobeasecretkey!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

###################################################################
######################## MODELS ###################################
# User class to log all registered users
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(80))

# Books class to log all entered books for each user
class Books(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    name = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return '<Books model {}>'.format(self.id)

################################################################################
############################# VIEWS  ###########################################
#Login protocol#
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
        # A simple database was set up where all books are entered
        # irrespective of the user.
        #making sure that users see only what is associated to their emails
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
def search():#
    if request.method == 'POST':
        if request.form.get('name'):
            _name = request.form.get("name")
            #making sure that users find only what is associated to their emails
            books = Books.query.filter_by(name=_name, email=current_user.email).all()
            return render_template('results.html',books=books)
        elif request.form.get('author'):
            _author = request.form.get("author")
            #making sure that users find only what is associated to their emails
            books = Books.query.filter_by(author=_author,email=current_user.email).all()
            return render_template('results.html',books=books)
        elif request.form.get('isbn'):
            _isbn = request.form.get("isbn")
            #making sure that users find only what is associated to their emails
            books = Books.query.filter_by(isbn=_isbn,email=current_user.email).all()
            return render_template('results.html',books=books)
        else:
            return render_template('search.html')
    else:
        return render_template('search.html')


#search results
@app.route('/results', methods=['GET'])
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

#initialization
if __name__ == '__main__':
    #website_url = 'bewerbungsaufgabe.increaseyourskills.com:443'
    #app.config['SERVER_NAME'] = website_url
    app.run(debug=True)
