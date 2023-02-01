from crypt import methods
import datetime
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




#ユーザー名、パスワード
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))
    def __init__(self, username, password):
        self.username = username
        self.password = password

#支出リスト
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



#トップページ
@app.route('/', methods=['POST', 'GET'])
def top():
    return render_template('top.html')

#サインアップ
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

#ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(days=1)
            login_user(user)
            return redirect('/a')
    else:
        if "username" in session:
            u = session["username"]
            user = User.query.filter_by(username=u).first()
            login_user(user)
            return redirect(url_for('a'))
        return render_template('login.html')

@app.route('/a', methods=['GET', 'POST'])
@login_required
def a():
    return render_template('a.html')

#現在の年月のリスト
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    today = datetime.date.today()
    session["today_year"] = today.year
    session["today_month"] = today.month
    today_year = int(session["today_year"])
    today_month = int(session["today_month"])

    session["category_col"] = ''

    if request.method == 'POST':
        up = request.form['up']
        if up == '1':
            if today_month==12:
                today_year += 1
                today_month = 1
            else:
                today_month += 1

        else:
            if today_month==1:
                today_year -= 1
                today_month = 12
            
            else:
                today_month -= 1

        return redirect(url_for('ind', today_year=today_year, today_month=today_month))

    elif request.method == 'GET':
        moneys = Money.query.filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category!='収入').order_by(desc(Money.use_date)).all()
        sum_price = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category!='収入').scalar()
        if sum_price is None:
            sum_price = 0
        incomes = Money.query.filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category=='収入').order_by(desc(Money.use_date)).all()
        sum_income = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category=='収入').scalar()
        if sum_income is None:
            sum_income = 0
        profit = sum_income - sum_price
        button_sel = 1

        return render_template('index.html', moneys=moneys, sum_price=sum_price, incomes=incomes, sum_income=sum_income, button_sel=button_sel, today_year=today_year, today_month=today_month, profit=profit)

#年月変更した時のリスト
@app.route('/index/<today_year>/<today_month>', methods=['POST', 'GET'])
@login_required
def ind(today_year, today_month):
    session["today_year"] = today_year
    session["today_month"] = today_month
    today_year = int(session["today_year"])
    today_month = int(session["today_month"])

    if "category_col" in session:
        category_col = session["category_col"]

    if request.method == 'POST':
        up = request.form['up']

        if up == '1':
            if today_month==12:
                today_year += 1
                today_month = 1
            else:
                today_month += 1

        else:
            if today_month==1:
                today_year -= 1
                today_month = 12
            
            else:
                today_month -= 1
        print(today_year, today_month)
        return redirect(url_for('ind', today_year=today_year, today_month=today_month))
        
    else:
        if category_col == '':
            moneys = Money.query.filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category!='収入').order_by(desc(Money.use_date)).all()
            sum_price = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category!='収入').scalar()
            if sum_price is None:
                sum_price = 0
            incomes = Money.query.filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category=='収入').order_by(desc(Money.use_date)).all()
            sum_income = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category=='収入').scalar()
            if sum_income is None:
                sum_income = 0
            profit = sum_income - sum_price
            button_sel = 2
        else:
            moneys = Money.query.filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category!='収入').filter(Money.use_category==category_col).order_by(desc(Money.use_date)).all()
            sum_price = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category!='収入').filter(Money.use_category==category_col).scalar()
            if sum_price is None:
                sum_price = 0
            incomes = Money.query.filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category=='収入').order_by(desc(Money.use_date)).all()
            sum_income = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username).filter(Money.year==today_year).filter(Money.month==today_month).filter(Money.use_category=='収入').scalar()
            if sum_income is None:
                sum_income = 0
            profit = sum_income - sum_price
            button_sel = 2

        return render_template('index.html', moneys=moneys, sum_price=sum_price, incomes=incomes, sum_income=sum_income, today_year=today_year, today_month=today_month, button_sel=button_sel, profit=profit)


#ログアウト
@app.route('/logout')
@login_required
def logout():
    session["username"] = current_user.username
    logout_user()
    return redirect('/')

#支出リストからの削除
@app.route('/delete', methods=['POST'])
@login_required
def delete():
    id = request.form["id"]
    list = Money.query.filter_by(id=id).first()
    db.session.delete(list)
    db.session.commit()

    today_year = session["today_year"]
    today_month = session["today_month"]

    return redirect(url_for('ind', today_year=today_year, today_month=today_month))


#リストに新規追加
@app.route('/new', methods=['POST', 'GET'])
@login_required
def new():
    if request.method == 'POST':
        username = current_user.username
        use_date = request.form.get('use_date')
        use_date = datetime.datetime.strptime(use_date, '%Y-%m-%d')
        use_category = request.form.get('use_category')
        detail_text = request.form.get('detail_text')
        price = request.form.get('price')
        year = int(use_date.year)
        month = int(use_date.month)

        detail = Money(username=username, use_date=use_date, use_category=use_category, detail_text=detail_text, price=price, year=year, month=month)
        db.session.add(detail)
        db.session.commit()

        today_year = session["today_year"]
        today_month = session["today_month"]

        return redirect(url_for('ind', today_year=today_year, today_month=today_month))

    else:
        return render_template('new.html')

#支出リストの更新
@app.route('/update', methods=['POST', 'GET'])
@login_required
def update():
    if request.method == 'POST':
        id = request.form["id"]
        list = Money.query.filter_by(id=id).one()

        return render_template('update.html', list=list)


@app.route('/u', methods=['POST', 'GET'])
@login_required
def u():
    if request.method == 'POST':
        id = request.form["id"]
        list = Money.query.filter_by(id=id).one()
        list.use_date = request.form["use_date"]
        list.use_date = datetime.datetime.strptime(list.use_date, '%Y-%m-%d')
        list.use_category = request.form["use_category"]
        list.detail_text = request.form["detail_text"]
        list.price = request.form["price"]
        list.year = int(list.use_date.year)
        list.month = int(list.use_date.month)          

        db.session.commit()

        today_year = session["today_year"]
        today_month = session["today_month"]
                
        return redirect(url_for('ind', today_year=today_year, today_month=today_month))

@app.route('/conditions', methods=['POST', 'GET'])
@login_required
def conditions():
    if request.method == 'POST':
        session["category_col"] = request.form.get('category_conditions')

        today_year = session["today_year"]
        today_month = session["today_month"]

        return redirect(url_for('ind', today_year=today_year, today_month=today_month))


if __name__=='__main__':
    app.run()