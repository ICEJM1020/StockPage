import requests
import os
import json as js
from flask import Flask, render_template, request, redirect, url_for
import threading
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

log = open("stockdata.log", "a+")
static_dir = os.path.join(BASE_DIR, 'static')
templates_dir = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__)

# 抓取的指数列表
indexlist = (
    's_sh000001',
    's_sz399001',
    's_sz399006',  # 前三

    'b_INDU',  # 道琼斯30种工业股票平均价格指数
    'b_CCMP',  # 纳斯达克综合指数
    'b_HSI',  # 恒生
    'b_NKY',  # 日经225指数

    'hf_XAU',  # 伦敦金
    'hf_XAG',  # 伦敦银
    'hf_CL',  # 纽约原油
    'hf_OIL',  # 布伦特原油
    'hf_S',  # 美国大豆
    'hf_C',  # 美国玉米

    'DINIW',  # 美元指数
    'fx_susdcny',  # 在岸人民币
    'fx_susdcnh',  # 离岸人民币（香港
    'fx_sjpycny',  # 日元兑人民币
    'fx_skrwcny',  # 韩元兑人民币
    'fx_sgbpcny',  # 英镑兑人民
    'fx_seurcny',  # 欧元兑人民币
    'fx_shkdcny',  # 港元兑人民币
    'fx_stwdcny',  # 台湾兑人民币

    'btc_btcbtcusd',  # 比特币美元
    'btc_btcethusd',  # 以太坊美元
    'btc_btcltcusd'  # 莱特币美元
)
JsonData = []


class myThread (threading.Thread):
    SleepTime = 60

    def __init__(self, threadID, name, counter, time):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.SleepTime = time

    def run(self):
        log.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"开始线程GetData\n")
        log.flush()
        getdata(self.SleepTime)

class StockData:
    def __init__(self, code):
        self.code = code
        self.name = None
        self.startprice = None
        self.endprice = None
        self.range = None  # 幅度
        self.ttv = None  # 成交量
        self.vof = None  # 成交额

        # 执行函数，自己创建对象,先判断是什么市场，再调用对应的函数
        self.iswhere()

    def iswhere(self):
        """判断是哪一种类型的数据"""
        if 's_' in self.code:
            self.cnindexdata()
        elif 'b_' in self.code:
            self.usindexdata()
        elif 'hf_' in self.code:
            self.fgindexdata()
        elif 'DINIW' in self.code:
            self.dollarindexdata()
        elif 'fx_' in self.code:
            self.foreignindexdata()
        elif 'btc_' in self.code:
            self.btcindexdata()

    # 构造request 获取数据
    def get_data(self):
        url = 'http://hq.sinajs.cn/list=' + str(self.code)
        data = requests.request(url=url, method='GET')
        return data.text

    # 格式转换，将获取的数据字符串拆分为列表的形式
    def formatconversion(self):
        datastring = self.get_data()
        datastring = datastring.replace('\"', ',')  # replace 不会改变元字符的内容
        datastring = datastring.split(',')
        del datastring[0]
        datastring.pop()
        return datastring

    # 获取和拆分国内指数数据
    def cnindexdata(self):
        datastring = self.formatconversion()
        # 对象赋值
        self.name = datastring[0]
        self.endprice = datastring[1]
        self.range = datastring[3]
        self.ttv = datastring[4]
        self.vof = datastring[5]

    # 获取美国和日本的指数
    def usindexdata(self):
        datastring = self.formatconversion()

        # 对象赋值
        self.name = datastring[0]
        self.endprice = datastring[1]
        self.range = datastring[3]

    # get futures good price
    def fgindexdata(self):
        datastring = self.formatconversion()
        self.name = datastring[len(datastring) - 1]
        self.endprice = datastring[0]
        self.range = datastring[1]

    # get dollar currency rate
    def dollarindexdata(self):
        datastring = self.formatconversion()
        self.name = datastring[9]
        self.endprice = datastring[1]
        d_range = (float(datastring[1]) - float(datastring[3])) / float(datastring[3]) * 100
        self.range = round(d_range, 2)

    # get foreign exchange
    def foreignindexdata(self):
        datastring = self.formatconversion()
        self.name = datastring[9]
        self.endprice = datastring[2]
        f_range = (float(datastring[2]) - float(datastring[3])) / float(datastring[3]) * 100
        self.range = round(f_range, 2)

    # 获取数字货币数据
    def btcindexdata(self):
        datastring = self.formatconversion()
        self.name = datastring[9]
        self.endprice = datastring[8]
        btc_range = (float(datastring[8]) - float(datastring[3])) / float(datastring[3]) * 100
        self.range = round(btc_range, 2)


# 下载图像
def downloadpic():
    url = ['http://image.sinajs.cn/newchart/min/n/sh000001.gif',
           'http://image.sinajs.cn/newchart/daily/n/sh000001.gif']
    header = {
        'User-Agent': "Mozilla/5.0(X11;Linux x86_64) AppleWebKit/537.36(KHTML, "
                      "like Gecko) Chrome / 72.0.3626.121 Safari/537.36"
    }
    for i in range(len(url)):
        pic = requests.request(url=url[i], method='GET', headers=header)
        #cur = datetime.datetime.today()
        title = "static/Data/" + str(i) + '_' + 'sh.gif';
        if pic.status_code == 200:
            #print("行情图片下载成功 ", i)
            with open(title, 'wb') as fp:
                fp.write(pic.content)
                fp.close()


def getdata(sleeptime):
    while True:
        for i in range(len(indexlist)):
            a = StockData(indexlist[i])
            JsonData.append({
                'num': str(indexlist[i]),
                'name': str(a.name),
                'price': str(float(a.endprice)),
                'range': a.range#str(float(a.range))
                    }
            )
        with open('static/Data/data.json', 'w') as f:
            js.dump(JsonData, f)
        downloadpic()
        log.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"get data success\n")
        log.flush()
        time.sleep(sleeptime)


@app.route("/stock/connection", methods=['GET', 'POST'])
def goconnetion():
    if request.method == 'GET':
        return render_template('connection.html')


@app.route("/stock", methods=['GET', 'POST'])
def gomainpage():
    if request.method == 'GET':
        return render_template('index.html')


@app.route("/")
def mainin():
    #redirect(url_for('gomainpage'))
    return redirect(url_for('gomainpage'))


if __name__ == '__main__':
    threadGet = myThread(1, "Thread-getData", 1, 600)
    threadGet.start()

    app.run("127.0.0.1", port=18637)
