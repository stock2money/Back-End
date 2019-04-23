from flask import Flask, request, json
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

# 配置数据库的地址
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost:3306/mydb'
# 跟踪数据库的修改，不建议开启
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(40), primary_key=True)
    stocks = db.Column(db.Text)


db.drop_all()
db.create_all()

@app.route('/api/login', methods=['POST'])
def login():
    code = request.form.to_dict()['code']
    res_wechat = requests.get("https://api.weixin.qq.com/sns/jscode2session?appid=wx25915d3c4f6a78f3&secret=133e74afeca06c60a597cf3b694a6c87&js_code="+code+ "&grant_type=authorization_code").json()
    res_jqdata = requests.post("https://dataapi.joinquant.com/apis", data=json.dumps({
        "method": "get_token",
        "mob": "15626401698",  # mob是申请JQData时所填写的手机号
        "pwd": "401698",  # Password为聚宽官网登录密码，新申请用户默认为手机号后6位
    }))
    res = {
        "openid": res_wechat['openid'],
        "token": res_jqdata.text
    }
    return json.dumps(res)

@app.route('/api/add', methods=['POST'])
def add_stock():
    form = request.form.to_dict()
    res = {'user': form['user'], 'stocks': []}
    query_result = User.query.filter_by(id=form['user']).first()
    stocks = get_stocks_list(query_result.stocks)
    if form['stock'] not in stocks:
        stocks.append(form['stock'])
        query_result.stocks = get_stocks_str(stocks)
        db.session.add(query_result)
        db.session.commit()
    res['stocks'] = stocks
    return json.dumps(res, ensure_ascii=False)


@app.route('/api/remove', methods=['POST'])
def remove_stock():
    form = request.form.to_dict()
    res = {'user': form['user'], 'stocks': []}
    query_result = User.query.filter_by(id=form['user']).first()
    stocks = get_stocks_list(query_result.stocks)
    if form['stock'] in stocks:
        stocks.remove(form['stock'])
        query_result.stocks = get_stocks_str(stocks)
        db.session.add(query_result)
        db.session.commit()
    res['stocks'] = stocks
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
    app.run()
