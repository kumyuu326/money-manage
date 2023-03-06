from crypt import methods
import datetime
import email
import os
from urllib.error import HTTPError
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from flask import Flask, render_template, request, redirect, session, url_for, make_response
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

TWILIO_ACCOUNT_SID="AC348d9e64b0f5495d684d1f190ae14093"
TWILIO_AUTH_TOKEN="25dfbc3d99a1700c5781644d3b58c7b4"
TWILIO_VERIFY_SERVICE="VAed40ddf358ba4cdac5d5a2fe363cea1d"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)



#ユーザー名、パスワード
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))
    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = password

#支出リスト
class Money(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50))
    use_date = db.Column(db.Date)
    use_category = db.Column(db.Text())
    use_detail = db.Column(db.Text())
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
        email = request.form.get('email')
        password = request.form.get('password')
        session['username'] = username
        session['email'] = email
        send_verification(email)

        user = User(username=username, email=email, password=generate_password_hash(password, method='sha256'))
        
        db.session.add(user)
        db.session.commit()
        return redirect('/verifyme')
    else:
        return render_template('signup.html')

def send_verification(email):
        verification = client.verify \
            .services(TWILIO_VERIFY_SERVICE) \
            .verifications \
            .create(to=email, channel='email')
        print(verification.sid)

@app.route('/verifyme', methods=['POST', 'GET'])
def generate_verification_code():
    error = None
    email = session['email']
    if request.method == 'POST':
        verification_code = request.form['verificationcode']
        if check_verification_token(email, verification_code):
            return redirect('/login')
        else:
            error = "Invalid verification code. Please try again."
            return render_template('verifypage.html', error = error)
    return render_template('verifypage.html', email = email)

def check_verification_token(phone, token):
    check = client.verify \
        .services(TWILIO_VERIFY_SERVICE) \
        .verification_checks \
        .create(to=phone, code=token)    
    return check.status == 'approved'

@app.route('/verifyme2', methods=['POST', 'GET'])
def generate_verification_code2():
    error = None
    email = session['email']
    if request.method == 'POST':
        verification_code = request.form['verificationcode']
        if check_verification_token(email, verification_code):
            return redirect('/graph')
        else:
            error = "Invalid verification code. Please try again."
            return render_template('verifypage.html', error = error)
    return render_template('verifypage.html', email = email)

#ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        session['username'] = username
        session['email'] = email
        send_verification(email)

        user = User.query.filter_by(username=username, email=email).first()
        if check_password_hash(user.password, password):
            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(days=1)
            login_user(user)
            session['user'] = 'T'
            return redirect('/verifyme2')
    else:
        if "user" in session:
            username = session["username"]
            user = User.query.filter_by(username=username).first()
            login_user(user)
            return redirect('/graph')
        return render_template('login.html')

@app.route('/graph', methods=['POST', 'GET'])
@login_required
def graph_now():
    today = datetime.date.today()
    session["today_year"] = today.year
    today_year = int(session["today_year"])
    button_sel = 1

    if request.method == 'POST':
        up = request.form['up']
        if up == '1':
            today_year += 1

        else:
            today_year -= 1

        return redirect(url_for('graph', today_year=today_year))
    
    graph_food_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==1).scalar()
    graph_daily_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==1).scalar()
    graph_tpt_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==1).scalar()
    graph_other_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==1).scalar()
    gf_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==1).scalar()
    gd_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==1).scalar()
    gt_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==1).scalar()

    graph_food_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==2).scalar()
    graph_daily_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==2).scalar()
    graph_tpt_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==2).scalar()
    graph_other_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==2).scalar()
    gf_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==2).scalar()
    gd_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==2).scalar()
    gt_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==2).scalar()

    graph_food_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==3).scalar()
    graph_daily_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==3).scalar()
    graph_tpt_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==3).scalar()
    graph_other_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==3).scalar()
    gf_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==3).scalar()
    gd_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==3).scalar()
    gt_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==3).scalar()

    graph_food_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==4).scalar()
    graph_daily_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==4).scalar()
    graph_tpt_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==4).scalar()
    graph_other_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==4).scalar()
    gf_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==4).scalar()
    gd_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==4).scalar()
    gt_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==4).scalar()

    graph_food_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==5).scalar()
    graph_daily_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==5).scalar()
    graph_tpt_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==5).scalar()
    graph_other_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==5).scalar()
    gf_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==5).scalar()
    gd_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==5).scalar()
    gt_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==5).scalar()

    graph_food_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==6).scalar()
    graph_daily_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==6).scalar()
    graph_tpt_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==6).scalar()
    graph_other_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==6).scalar()
    gf_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==6).scalar()
    gd_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==6).scalar()
    gt_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==6).scalar()

    graph_food_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==7).scalar()
    graph_daily_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==7).scalar()
    graph_tpt_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==7).scalar()
    graph_other_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==7).scalar()
    gf_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==7).scalar()
    gd_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==7).scalar()
    gt_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==7).scalar()

    graph_food_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==8).scalar()
    graph_daily_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==8).scalar()
    graph_tpt_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==8).scalar()
    graph_other_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==8).scalar()
    gf_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==8).scalar()
    gd_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==8).scalar()
    gt_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==8).scalar()

    graph_food_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==9).scalar()
    graph_daily_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==9).scalar()
    graph_tpt_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==9).scalar()
    graph_other_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==9).scalar()
    gf_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==9).scalar()
    gd_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==9).scalar()
    gt_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==9).scalar()

    graph_food_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==10).scalar()
    graph_daily_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==10).scalar()
    graph_tpt_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==10).scalar()
    graph_other_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==10).scalar()
    gf_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==10).scalar()
    gd_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==10).scalar()
    gt_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==10).scalar()

    graph_food_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==11).scalar()
    graph_daily_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==11).scalar()
    graph_tpt_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==11).scalar()
    graph_other_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==11).scalar()
    gf_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==11).scalar()
    gd_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==11).scalar()
    gt_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==11).scalar()

    graph_food_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==12).scalar()
    graph_daily_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==12).scalar()
    graph_tpt_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==12).scalar()
    graph_other_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==12).scalar()
    gf_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==12).scalar()
    gd_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==12).scalar()
    gt_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==12).scalar()

    graph2_food = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year).scalar()
    if graph2_food is None:
        graph2_food = 0
    graph2_daily = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year).scalar()
    if graph2_daily is None:
        graph2_daily = 0
    graph2_tpt = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year).scalar()
    if graph2_tpt is None:
        graph2_tpt = 0
    graph2_other = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year).scalar()
    if graph2_other is None:
        graph2_other = 0

    graph2_money = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category!='収入', Money.year==today_year).scalar()
    if graph2_money is None:
        graph2_money = 0

    return render_template('a.html', graph_food_1=graph_food_1, graph_daily_1=graph_daily_1, graph_other_1=graph_other_1, graph_food_2=graph_food_2, graph_daily_2=graph_daily_2, graph_other_2=graph_other_2, graph_food_3=graph_food_3, graph_daily_3=graph_daily_3, 
                                graph_other_3=graph_other_3, graph_food_4=graph_food_4, graph_daily_4=graph_daily_4, graph_other_4=graph_other_4, graph_food_5=graph_food_5, graph_daily_5=graph_daily_5, graph_other_5=graph_other_5, graph_food_6=graph_food_6,
                                    graph_daily_6=graph_daily_6, graph_other_6=graph_other_6, graph_food_7=graph_food_7, graph_daily_7=graph_daily_7, graph_other_7=graph_other_7, graph_food_8=graph_food_8, graph_daily_8=graph_daily_8, graph_other_8=graph_other_8,
                                        graph_food_9=graph_food_9, graph_daily_9=graph_daily_9, graph_other_9=graph_other_9, graph_food_10=graph_food_10, graph_daily_10=graph_daily_10, graph_other_10=graph_other_10, graph_food_11=graph_food_11, graph_daily_11=graph_daily_11, 
                                            graph_other_11=graph_other_11, graph_food_12=graph_food_12, graph_daily_12=graph_daily_12, graph_other_12=graph_other_12, 
                                                graph_tpt_1=graph_tpt_1, graph_tpt_2=graph_tpt_2, graph_tpt_3=graph_tpt_3, graph_tpt_4=graph_tpt_4, graph_tpt_5=graph_tpt_5, graph_tpt_6=graph_tpt_6, graph_tpt_7=graph_tpt_7, graph_tpt_8=graph_tpt_8, graph_tpt_9=graph_tpt_9, graph_tpt_10=graph_tpt_10, graph_tpt_11=graph_tpt_11, graph_tpt_12=graph_tpt_12,
                                                    graph2_food=graph2_food, graph2_daily=graph2_daily, graph2_tpt=graph2_tpt, graph2_other=graph2_other, graph2_money=graph2_money,
                                                        gf_1=gf_1, gf_2=gf_2, gf_3=gf_3, gf_4=gf_4, gf_5=gf_5, gf_6=gf_6, gf_7=gf_7, gf_8=gf_8, gf_9=gf_9, gf_10=gf_10, gf_11=gf_11, gf_12=gf_12,
                                                            gd_1=gd_1, gd_2=gd_2, gd_3=gd_3, gd_4=gd_4, gd_5=gd_5, gd_6=gd_6, gd_7=gd_7, gd_8=gd_8, gd_9=gd_9, gd_10=gd_10, gd_11=gd_11, gd_12=gd_12,
                                                                gt_1=gt_1, gt_2=gt_2, gt_3=gt_3, gt_4=gt_4, gt_5=gt_5, gt_6=gt_6, gt_7=gt_7, gt_8=gt_8, gt_9=gt_9, gt_10=gt_10, gt_11=gt_11, gt_12=gt_12,
                                                                    button_sel=button_sel, today_year=today_year)

@app.route('/graph/<today_year>', methods=['POST', 'GET'])
@login_required
def graph(today_year):
    session["today_year"] = today_year
    today_year = int(session["today_year"])
    button_sel = 2

    if request.method == 'POST':
        up = request.form['up']
        if up == '1':
            today_year += 1

        else:
            today_year -= 1

        return redirect(url_for('graph', today_year=today_year))
    
    graph_food_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==1).scalar()
    graph_daily_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==1).scalar()
    graph_tpt_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==1).scalar()
    graph_other_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==1).scalar()
    gf_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==1).scalar()
    gd_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==1).scalar()
    gt_1 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==1).scalar()

    graph_food_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==2).scalar()
    graph_daily_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==2).scalar()
    graph_tpt_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==2).scalar()
    graph_other_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==2).scalar()
    gf_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==2).scalar()
    gd_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==2).scalar()
    gt_2 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==2).scalar()

    graph_food_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==3).scalar()
    graph_daily_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==3).scalar()
    graph_tpt_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==3).scalar()
    graph_other_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==3).scalar()
    gf_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==3).scalar()
    gd_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==3).scalar()
    gt_3 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==3).scalar()

    graph_food_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==4).scalar()
    graph_daily_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==4).scalar()
    graph_tpt_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==4).scalar()
    graph_other_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==4).scalar()
    gf_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==4).scalar()
    gd_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==4).scalar()
    gt_4 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==4).scalar()

    graph_food_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==5).scalar()
    graph_daily_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==5).scalar()
    graph_tpt_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==5).scalar()
    graph_other_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==5).scalar()
    gf_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==5).scalar()
    gd_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==5).scalar()
    gt_5 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==5).scalar()

    graph_food_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==6).scalar()
    graph_daily_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==6).scalar()
    graph_tpt_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==6).scalar()
    graph_other_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==6).scalar()
    gf_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==6).scalar()
    gd_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==6).scalar()
    gt_6 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==6).scalar()

    graph_food_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==7).scalar()
    graph_daily_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==7).scalar()
    graph_tpt_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==7).scalar()
    graph_other_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==7).scalar()
    gf_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==7).scalar()
    gd_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==7).scalar()
    gt_7 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==7).scalar()

    graph_food_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==8).scalar()
    graph_daily_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==8).scalar()
    graph_tpt_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==8).scalar()
    graph_other_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==8).scalar()
    gf_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==8).scalar()
    gd_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==8).scalar()
    gt_8 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==8).scalar()

    graph_food_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==9).scalar()
    graph_daily_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==9).scalar()
    graph_tpt_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==9).scalar()
    graph_other_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==9).scalar()
    gf_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==9).scalar()
    gd_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==9).scalar()
    gt_9 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==9).scalar()

    graph_food_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==10).scalar()
    graph_daily_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==10).scalar()
    graph_tpt_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==10).scalar()
    graph_other_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==10).scalar()
    gf_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==10).scalar()
    gd_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==10).scalar()
    gt_10 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==10).scalar()

    graph_food_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==11).scalar()
    graph_daily_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==11).scalar()
    graph_tpt_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==11).scalar()
    graph_other_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==11).scalar()
    gf_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==11).scalar()
    gd_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==11).scalar()
    gt_11 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==11).scalar()

    graph_food_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year, Money.month==12).scalar()
    graph_daily_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year, Money.month==12).scalar()
    graph_tpt_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year, Money.month==12).scalar()
    graph_other_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year, Money.month==12).scalar()
    gf_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year-1, Money.month==12).scalar()
    gd_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year-1, Money.month==12).scalar()
    gt_12 = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year-1, Money.month==12).scalar()

    graph2_food = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='食費', Money.year==today_year).scalar()
    if graph2_food is None:
        graph2_food = 0
    graph2_daily = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='日用品', Money.year==today_year).scalar()
    if graph2_daily is None:
        graph2_daily = 0
    graph2_tpt = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='交通費', Money.year==today_year).scalar()
    if graph2_tpt is None:
        graph2_tpt = 0
    graph2_other = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category=='その他', Money.year==today_year).scalar()
    if graph2_other is None:
        graph2_other = 0

    graph2_money = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.use_category!='収入', Money.year==today_year).scalar()
    if graph2_money is None:
        graph2_money = 0

    return render_template('a.html', graph_food_1=graph_food_1, graph_daily_1=graph_daily_1, graph_other_1=graph_other_1, graph_food_2=graph_food_2, graph_daily_2=graph_daily_2, graph_other_2=graph_other_2, graph_food_3=graph_food_3, graph_daily_3=graph_daily_3, 
                                graph_other_3=graph_other_3, graph_food_4=graph_food_4, graph_daily_4=graph_daily_4, graph_other_4=graph_other_4, graph_food_5=graph_food_5, graph_daily_5=graph_daily_5, graph_other_5=graph_other_5, graph_food_6=graph_food_6,
                                    graph_daily_6=graph_daily_6, graph_other_6=graph_other_6, graph_food_7=graph_food_7, graph_daily_7=graph_daily_7, graph_other_7=graph_other_7, graph_food_8=graph_food_8, graph_daily_8=graph_daily_8, graph_other_8=graph_other_8,
                                        graph_food_9=graph_food_9, graph_daily_9=graph_daily_9, graph_other_9=graph_other_9, graph_food_10=graph_food_10, graph_daily_10=graph_daily_10, graph_other_10=graph_other_10, graph_food_11=graph_food_11, graph_daily_11=graph_daily_11, 
                                            graph_other_11=graph_other_11, graph_food_12=graph_food_12, graph_daily_12=graph_daily_12, graph_other_12=graph_other_12, 
                                                graph_tpt_1=graph_tpt_1, graph_tpt_2=graph_tpt_2, graph_tpt_3=graph_tpt_3, graph_tpt_4=graph_tpt_4, graph_tpt_5=graph_tpt_5, graph_tpt_6=graph_tpt_6, graph_tpt_7=graph_tpt_7, graph_tpt_8=graph_tpt_8, graph_tpt_9=graph_tpt_9, graph_tpt_10=graph_tpt_10, graph_tpt_11=graph_tpt_11, graph_tpt_12=graph_tpt_12,
                                                    graph2_food=graph2_food, graph2_daily=graph2_daily, graph2_tpt=graph2_tpt, graph2_other=graph2_other, graph2_money=graph2_money,
                                                        gf_1=gf_1, gf_2=gf_2, gf_3=gf_3, gf_4=gf_4, gf_5=gf_5, gf_6=gf_6, gf_7=gf_7, gf_8=gf_8, gf_9=gf_9, gf_10=gf_10, gf_11=gf_11, gf_12=gf_12,
                                                            gd_1=gd_1, gd_2=gd_2, gd_3=gd_3, gd_4=gd_4, gd_5=gd_5, gd_6=gd_6, gd_7=gd_7, gd_8=gd_8, gd_9=gd_9, gd_10=gd_10, gd_11=gd_11, gd_12=gd_12,
                                                                gt_1=gt_1, gt_2=gt_2, gt_3=gt_3, gt_4=gt_4, gt_5=gt_5, gt_6=gt_6, gt_7=gt_7, gt_8=gt_8, gt_9=gt_9, gt_10=gt_10, gt_11=gt_11, gt_12=gt_12,
                                                                    button_sel=button_sel, today_year=today_year)


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
        moneys = Money.query.filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category!='収入').order_by(desc(Money.use_date)).all()
        blank_moneys = 0
        if len(moneys) < 11:
            blank_moneys = 11 - len(moneys)
        sum_price = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category!='収入').scalar()
        if sum_price is None:
            sum_price = 0
        incomes = Money.query.filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category=='収入').order_by(desc(Money.use_date)).all()
        blank_incomes = 0
        if len(incomes) < 11:
            blank_incomes = 11 - len(incomes)
        sum_income = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category=='収入').scalar()
        if sum_income is None:
            sum_income = 0
        profit = sum_income - sum_price
        button_sel = 1

        return render_template('index.html', moneys=moneys, sum_price=sum_price, incomes=incomes, sum_income=sum_income, button_sel=button_sel, today_year=today_year, today_month=today_month, profit=profit, blank_moneys=blank_moneys, blank_incomes=blank_incomes)

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
            moneys = Money.query.filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category!='収入').order_by(desc(Money.use_date)).all()
            blank_moneys = 0
            if len(moneys) < 11:
                blank_moneys = 11 - len(moneys)
            sum_price = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category!='収入').scalar()
            if sum_price is None:
                sum_price = 0
            incomes = Money.query.filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category=='収入').order_by(desc(Money.use_date)).all()
            blank_incomes = 0
            if len(incomes) < 11:
                blank_incomes = 11 - len(incomes)
            sum_income = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category=='収入').scalar()
            if sum_income is None:
                sum_income = 0
            profit = sum_income - sum_price
            button_sel = 2
        else:
            moneys = Money.query.filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category!='収入', Money.use_category==category_col).order_by(desc(Money.use_date)).all()
            blank_moneys = 0
            if len(moneys) < 11:
                blank_moneys = 11 - len(moneys)
            sum_price = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category!='収入', Money.use_category==category_col).scalar()
            if sum_price is None:
                sum_price = 0
            incomes = Money.query.filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category=='収入').order_by(desc(Money.use_date)).all()
            blank_incomes = 0
            if len(incomes) < 11:
                blank_incomes = 11 - len(incomes)
            sum_income = db.session.query(func.sum(Money.price)).filter(Money.username==current_user.username, Money.year==today_year, Money.month==today_month, Money.use_category=='収入').scalar()
            if sum_income is None:
                sum_income = 0
            profit = sum_income - sum_price
            button_sel = 2

        return render_template('index.html', moneys=moneys, sum_price=sum_price, incomes=incomes, sum_income=sum_income, today_year=today_year, today_month=today_month, button_sel=button_sel, profit=profit, blank_moneys=blank_moneys, blank_incomes=blank_incomes)


#ログアウト
@app.route('/logout')
@login_required
def logout():
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
        use_category, use_detail = request.form.get('use_category').split()
        detail_text = request.form.get('detail_text')
        price = request.form.get('price')
        year = int(use_date.year)
        month = int(use_date.month)

        detail = Money(username=username, use_date=use_date, use_category=use_category, use_detail=use_detail, detail_text=detail_text, price=price, year=year, month=month)
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
    app.run(debug=True)