import os
import time
from flask import Flask, request, json
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

# 配置数据库的地址
# window 10
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost:3306/mydb'

# centos
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost:3306/mydb'

# 跟踪数据库的修改，不建议开启
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(40), primary_key=True)
    stocks = db.Column(db.Text)
    isVip = db.Column(db.Boolean, default=False)

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


# 登陆
@app.route('/api/login', methods=['POST'])
def login():
    # 通过code获取openid
    code = request.json['code']
    res_wechat = requests.get("https://api.weixin.qq.com/sns/jscode2session?appid=wx25915d3c4f6a78f3&secret=133e74afeca06c60a597cf3b694a6c87&js_code="+code+ "&grant_type=authorization_code").json()

    # 获取jq的token
    res_jqdata = requests.post("https://dataapi.joinquant.com/apis", data=json.dumps({
        "method": "get_current_token",
        "mob": "15626401698",  # mob是申请JQData时所填写的手机号
        "pwd": "401698",  # Password为聚宽官网登录密码，新申请用户默认为手机号后6位
    }))

    res = {
        "openid": '',
        "token": '',
        "msg": '',
        "stocks": []
    }

    # 依据微信服务器返回处理信息
    if "errcode" not in res_wechat:
        res["openid"] = res_wechat["openid"]
        res["token"] = res_jqdata.text
        query_result = User.query.filter_by(id=res_wechat["openid"]).first()
        if not query_result:
            user = User(id=res_wechat["openid"])
            db.session.add(user)
            db.session.commit()
        else:
            res['stocks'] = get_stocks_list(query_result.stocks)
    else:
        res["msg"] = res_wechat["errmsg"]

    return json.dumps(res)


# vip校验
@app.route('/api/user/vip', methods=['POST'])
def vip_check():
    info = request.json()
    res = {'userId': info['userId'], 'status': False, 'msg': ''}
    try:
        vipCode = info["vipCode"]
        if vipCode == "sysu":
            try:
                query_result = User.query.filter_by(id=info['userId']).first()
                query_result.isVip = True
                db.session.add(query_result)
                db.session.commit()
            except BaseException as e:
                print(e)
                res["msg"] = "An unknown error occurred, please try again later"
        else:
            res["msg"] = "Vip code is invalid"
    except BaseException as e:
        print(e)
        res["msg"] = "Incorrect parameter"
    return json.dumps(res, ensure_ascii=False)


# 添加自选股
@app.route('/api/stocks/add', methods=['POST'])
def add_stock():
    res = {'userId': '', 'stocks': [], 'msg': ''}
    try:
        id = request.json['userId']
        code = request.json['stockCode']
        res['userId'] = id
        query_result = User.query.filter_by(id=id).first()
        if query_result == None:
            res["msg"] = "No such a user"
        else:
            stocks = get_stocks_list(query_result.stocks)
            if code not in stocks:
                stocks.append(code)
                query_result.stocks = get_stocks_str(stocks)
                db.session.add(query_result)
                db.session.commit()
            res['stocks'] = stocks
    except BaseException as e:
        print(e)
        res["msg"] = "Incorrect parameter"
    return json.dumps(res, ensure_ascii=False)


# 取消自选股
@app.route('/api/stocks/remove', methods=['POST'])
def remove_stock():
    res = {'userId': '', 'stocks': [], 'msg': ''}
    try:
        id = request.json['userId']
        code = request.json['stockCode']
        query_result = User.query.filter_by(id=id).first()
        if query_result == None:
            res["msg"] = "No such a user"
        else:
            stocks = get_stocks_list(query_result.stocks)
            if code in stocks:
                stocks.remove(code)
                query_result.stocks = get_stocks_str(stocks)
                db.session.add(query_result)
                db.session.commit()
            res['stocks'] = stocks
    except BaseException as e:
        print(e)
        res["msg"] = "Incorrect parameter"
    return json.dumps(res, ensure_ascii=False)


# 获取新闻
@app.route('/api/news', methods=['GET'])
def get_news():
    s = int(request.args.get('from'))
    e = int(request.args.get('to'))
    res = {"from": s, "to": e, "data": [], "msg": ''}
    try:
        if(s >= 0 and e >= s):
            news = News.query.order_by(db.desc(News.time)).offset(s).limit(e)
            data = []
            for n in news:
                model = {"time": n.time, "title": n.title, "detail": n.detail}
                data.append(model)
            res["data"] = data
    except BaseException as e:
        print(e)
        res["msg"] = "Incorrect parameter"
    return json.dumps(res, ensure_ascii=False)


# 获取指定用户的自选股信息
@app.route('/api/stocks/<userId>', methods=['GET'])
def get_stocks(userId):
    query_result = User.query.filter_by(id=userId).first()
    res = {'userId': userId, 'stocks': [], 'msg': ''}
    if not query_result:
        user = User(id=userId)
        db.session.add(user)
        db.session.commit()
    else:
        res['stocks'] = get_stocks_list(query_result.stocks)
    return json.dumps(res, ensure_ascii=False)


# 获取所有股票
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
