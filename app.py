from flask import Flask, request, json
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

# 配置数据库的地址
# window 10
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost:3306/mydb'

# centos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost:3306/mydb'

# 跟踪数据库的修改，不建议开启
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(40), primary_key=True)
    stocks = db.Column(db.Text)

class News(db.Model):
    __tablename__ = 'news'
    time = db.Column(db.String(30), primary_key=True)
    title = db.Column(db.String(200), primary_key=True)
    href = db.Column(db.String(100))
    detail = db.Column(db.Text)

class Stock(db.Model):
    __tablename__ = 'stock'
    code = db.Column(db.String(30), primary_key=True)
    name = db.Column(db.String(200))
    display_name = db.Column(db.String(100))
    type = db.Column(db.String(20))

# db.drop_all()
# db.create_all()

@app.route('/api/login', methods=['POST'])
def login():
    code = request.json['code']
    res_wechat = requests.get("https://api.weixin.qq.com/sns/jscode2session?appid=wx25915d3c4f6a78f3&secret=133e74afeca06c60a597cf3b694a6c87&js_code="+code+ "&grant_type=authorization_code").json()
    res_jqdata = requests.post("https://dataapi.joinquant.com/apis", data=json.dumps({
        "method": "get_token",
        "mob": "15626401698",  # mob是申请JQData时所填写的手机号
        "pwd": "401698",  # Password为聚宽官网登录密码，新申请用户默认为手机号后6位
    }))
    res = {
        "openid": '',
        "token": '',
        "msg": ''
    }

    if res_wechat['errcode'] == 0:
        res["openid"] = res_wechat["openid"]
        res["token"] = res_jqdata.text
    else:
        res["msg"] = res_wechat["errmsg"]

    return json.dumps(res)

@app.route('/api/add', methods=['POST'])
def add_stock():
    try:
        form = request.json
        res = {'user': form['user'], 'stocks': []}
        query_result = User.query.filter_by(id=form['user']).first()
        stocks = get_stocks_list(query_result.stocks)
        if form['stock'] not in stocks:
            stocks.append(form['stock'])
            query_result.stocks = get_stocks_str(stocks)
            db.session.add(query_result)
            db.session.commit()
        res['stocks'] = stocks
    except BaseException as e:
        print(e)
        res["msg"] = "Incorrect parameter"
    return json.dumps(res, ensure_ascii=False)


@app.route('/api/remove', methods=['POST'])
def remove_stock():
    form = request.json
    res = {'user': form['user'], 'stocks': [], 'msg': ''}
    try:
        query_result = User.query.filter_by(id=form['user']).first()
        stocks = get_stocks_list(query_result.stocks)
        if form['stock'] in stocks:
            stocks.remove(form['stock'])
            query_result.stocks = get_stocks_str(stocks)
            db.session.add(query_result)
            db.session.commit()
        res['stocks'] = stocks
    except BaseException as e:
        print(e)
        res["msg"] = "Incorrect parameter"
    return json.dumps(res, ensure_ascii=False)

@app.route('/api/news', methods=['GET'])
def get_news():
    res = []
    news = News.query.all()
    for n in news:
        model = {"time": n.time, "title": n.title, "detail": n.detail}
        res.append(model)
    return json.dumps(res, ensure_ascii=False)

@app.route('/api/<username>', methods=['GET'])
def get_stocks(username):
    query_result = User.query.filter_by(id=username).first()
    res = {'user': username, 'stocks': []}
    if not query_result:
        user = User(id=username)
        db.session.add(user)
        db.session.commit()
    else:
        res['stocks'] = get_stocks_list(query_result.stocks)
    return json.dumps(res, ensure_ascii=False)


def get_all_stocks_info():

    # 获取token
    res_jqdata_token = requests.post("https://dataapi.joinquant.com/apis", data=json.dumps({
        "method": "get_token",
        "mob": "15626401698",  # mob是申请JQData时所填写的手机号
        "pwd": "401698",  # Password为聚宽官网登录密码，新申请用户默认为手机号后6位
    }))
    token = res_jqdata_token.text

    # 获取股票相关信息
    res_jqdata_stocks = requests.post("https://dataapi.joinquant.com/apis", data=json.dumps({
        "method": "get_all_securities",
        "token": token,
        "code": "stock",
        "date": "2019-01-15"
    }))
    # 信息处理
    stocks = res_jqdata_stocks.text.split('\n')
    all_stock_info = []
    for i, stock in enumerate(stocks):
        if i >= 1:
            info = stock.split(',')
            stock_info = Stock(name=info[2], display_name=info[1], code=info[0], type=info[5])
            all_stock_info.append(stock_info)
    db.session.add_all(all_stock_info)
    db.session.commit()

# get_all_stocks_info()


def get_stocks_list(stocks):
    print(stocks)
    if stocks is None:
        return []
    else:
        return stocks.split()

def get_stocks_str(stocks_list):
    str = ''
    for stock in stocks_list:
        str += stock + ' '
    return str

if __name__ == '__main__':
    app.run(host="0.0.0.0")
