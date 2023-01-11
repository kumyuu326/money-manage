from crypt import methods
from datetime import datetime, date
import os
from flask import Flask, render_template, request, redirect, session, url_for
from flask_login import UserMixin, LoginManager, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)
db = SQLAlchemy(app)




class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Money(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50))
    use_date = db.Column(db.Date)
    use_category = db.Column(db.Text())
    detail_text = db.Column(db.Text())
    price = db.Column(db.Integer)
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)
    
db.create_all()



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['POST', 'GET'])
def top():
    return render_template('top.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = User(username=username, password=generate_password_hash(password, method='sha256'))
        
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect('/index')
    else:
        return render_template('login.html')

@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    moneys = Money.query.filter(Money.username==current_user.username).order_by(desc(Money.use_date)).all()
    sum_price = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username).scalar()
    return render_template('index.html', moneys=moneys, sum_price=sum_price)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/delete', methods=['POST'])
@login_required
def delete():
    id = request.form["id"]
    list = Money.query.filter_by(id=id).first()
    db.session.delete(list)
    db.session.commit()
    return redirect('/index')

@app.route('/new', methods=['POST', 'GET'])
@login_required
def new():
    if request.method == 'POST':
        username = current_user.username
        use_date = request.form.get('use_date')
        use_date = datetime.strptime(use_date, '%Y-%m-%d')
        use_category = request.form.get('use_category')
        detail_text = request.form.get('detail_text')
        price = request.form.get('price')
        year = int(use_date.year)
        month = int(use_date.month)

        detail = Money(username=username, use_date=use_date, use_category=use_category, detail_text=detail_text, price=price, year=year, month=month)
        db.session.add(detail)
        db.session.commit()

        return redirect('/index')

@app.route('/conditions', methods=['POST', 'GET'])
@login_required
def conditions():
        if request.method == 'POST':
            year_con = request.form.get('year_conditions')
            month_con = request.form.get('month_conditions')
            category_con = request.form.get('category_conditions')
            if year_con== '' and month_con == '' and category_con == '':
                moneys = Money.query.filter(Money.username==current_user.username).order_by(desc(Money.use_date)).all()
                sum_price = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username).scalar()

            elif year_con != '' and month_con =='' and category_con == '':
                moneys = Money.query.filter(Money.username==current_user.username).filter(Money.year==int(year_con)).order_by(desc(Money.use_date)).all()
                sum_price = db.session.query(func.sum(Money.price)).filter(Money.year==int(year_con)).filter(Money.username==current_user.username).scalar()         

            elif year_con == '' and month_con != '' and category_con == '':
                moneys = Money.query.filter(Money.username==current_user.username).filter(Money.month==int(month_con)).order_by(desc(Money.use_date)).all()
                sum_price = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username).filter(Money.month==int(month_con)).scalar()

            elif year_con == '' and month_con == '' and category_con != '':
                moneys = Money.query.filter(Money.use_category==category_con).filter(Money.username==current_user.username).order_by(desc(Money.use_date)).all()
                sum_price = db.session.query(func.sum(Money.price)).filter(Money.use_category==category_con).filter(Money.username==current_user.username).scalar()

            elif year_con != '' and month_con != '' and category_con == '':
                moneys = Money.query.filter(Money.year==int(year_con)).filter(Money.month==int(month_con)).filter(Money.username==current_user.username).order_by(desc(Money.use_date)).all()
                sum_price = db.session.query(func.sum(Money.price)).filter(Money.year==int(year_con)).filter(Money.month==int(month_con)).filter(Money.username==current_user.username).scalar()
            
            elif year_con != '' and month_con == '' and category_con != '':
                moneys = Money.query.filter(Money.year==int(year_con)).filter(Money.use_category==category_con).filter(Money.username==current_user.username).order_by(desc(Money.use_date)).all()
                sum_price = db.session.query(func.sum(Money.price)).filter(Money.year==int(year_con)).filter(Money.use_category==category_con).filter(Money.username==current_user.username).scalar()

            elif year_con == '' and month_con != '' and category_con != '':
                moneys = Money.query.filter(Money.month==int(month_con)).filter(Money.use_category==category_con).filter(Money.username==current_user.username).order_by(desc(Money.use_date)).all()
                sum_price = db.session.query(func.sum(Money.price)).filter(Money.month==int(month_con)).filter(Money.use_category==category_con).filter(Money.username==current_user.username).scalar()

            else:
                moneys = Money.query.filter(Money.username==current_user.username).filter(Money.year==int(year_con)).filter(Money.month==int(month_con)).filter(Money.use_category==category_con).order_by(desc(Money.use_date)).all()
                sum_price = db.session.query(func.sum(Money.price)).filter(Money.year==int(year_con)).filter(Money.month==int(month_con)).filter(Money.use_category==category_con).filter(Money.username==current_user.username).scalar()         
            return render_template('index.html', moneys=moneys, sum_price=sum_price)

@app.route('/update', methods=['POST', 'GET'])
@login_required
def update():
    if request.method == 'POST':
        id = request.form["id"]
        list = Money.query.filter_by(id=id).one()
        if list.price < 0:
            list.price = str(int(list.price)*-1)

        return render_template('update.html', list=list)

@app.route('/u', methods=['POST', 'GET'])
@login_required
def u():
    if request.method == 'POST':
        id = request.form["id"]
        list = Money.query.filter_by(id=id).one()
        list.use_date = request.form["use_date"]
        list.use_date = datetime.strptime(list.use_date, '%Y-%m-%d')
        list.use_category = request.form["use_category"]
        list.detail_text = request.form["detail_text"]
        list.price = request.form["price"]
        list.year = int(list.use_date.year)
        list.month = int(list.use_date.month)

        db.session.commit()
        return redirect('/index')


if __name__=='__main__':
    app.run()