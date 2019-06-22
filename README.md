# stock2money.server



## 开发环境

* Python 3.x
* Window 10 和 Centos 7 
* MySQL
* Flask 1.0.2

> 在相应的开发系统上需要分别选择对应数据库的配置



## 运行

* `python -m flask run`
* [运行参考](https://blog.csdn.net/lllllyt/article/details/89762844)



## API说明

* [API文档](https://github.com/stock2money/Dashboard/blob/master/API.md)


## MySQL

```sql
CREATE DATABASE if not EXISTS mydb;
use mydb;


create table if not exists comment(
    code varchar(20) not NULL,
	time varchar(30) not null,
    title varchar(200) not null,
    href varchar(100) not null,
    detail text not null,
    author varchar(50) not null,
    avatar varchar(200),
    emotion int,
    primary key(code, author, title)
) charset=utf8;

create table if not exists news(
	time varchar(30) not null,
    title varchar(200) not null,
    href varchar(100) not null,
    detail text not null,
    primary key(time, title)
) charset=utf8;
```
