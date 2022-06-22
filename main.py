import json
import os
import re
import sys
import csv
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

sys.path.append("D:\Tinysoft\Analyse.NET")
import TSLPy3 as ts

work_dir = "D:\\ts\\"


def tsbytestostr(data):
    if isinstance(data, tuple) or isinstance(data, list):
        lent = len(data)
        ret = []

        for i in range(lent):
            ret.append(tsbytestostr(data[i]))
    elif isinstance(data, dict):
        lent = len(data)
        ret = {}
        for i in data:
            ret[tsbytestostr(i)] = tsbytestostr(data[i])
    elif isinstance(data, bytes):
        ret = data.decode('gbk', errors='ignore')
    else:
        ret = data
    return ret


def F执行函数(func_name, pmlist):
    if not ts.Logined():
        F连接服务器()
    data1 = ts.RemoteCallFunc(func_name,
                              pmlist, {})
    data1 = tsbytestostr(data1[1])
    return data1


def F执行语句(ts_str, pmdict=None, unencode=True):
    if not ts.Logined():
        F连接服务器()

    if pmdict is not None:
        ts_str1 = ts_str.format(**pmdict)
        datar = ts.RemoteExecute(ts_str1, {})
    else:
        datar = ts.RemoteExecute(ts_str, {})
    data1 = datar[1]
    if not unencode:
        return data1
    if type(data1) == bytes:
        data1 = json.loads(data1)
    if type(data1) != list:
        print('F执行语句不是list', tsbytestostr(datar), ts_str)
        return []
    return data1


def F生成天软日期_str(one_day: str):
    one_day = re.split('[-/]', one_day)
    ts_day = ts.EncodeDate(int(one_day[0]), int(one_day[1]), int(one_day[2]))
    return ts_day


def F读取脚本文件(filename):
    with open(work_dir + filename, 'r', encoding='utf-8') as f:
        ts_str = f.read()
    return ts_str


def F连接服务器(b配置文件=True):
    if not ts.Logined():
        if b配置文件:
            dl = ts.DefaultConnectAndLogin("test")
        else:
            ts.ConnectServer("219.143.214.209", 888)
            # ts.ConnectServer("211.100.23.205",443)
            dl = ts.LoginServer("liuzhiyong", "Zoos_600809")  # Tuple(ErrNo,ErrMsg) 登陆用户
        if dl[0] == 0:
            print("登陆成功")
            print("服务器设置:", ts.GetService())
            ts.SetComputeBitsOption(64)  # 设置计算单位
            print("计算位数设置:", ts.GetComputeBitsOption())
            data = ts.RemoteExecute("return 'return a string';", {})  # 执行一条语句
            print("数据:", data)
        else:
            print("登陆失败", tsbytestostr(dl[1]))
        return
    print('已连接,无需重连')


def F断开服务器():
    if ts.Logined():
        ts.Disconnect()  # 断开连接
        print('断开成功')
    print('未连接,无需断开')


code_rank = F读取脚本文件("rank.js")


def count_one_day_score(day, num, pc, sc, date_str):
    ts_data = F执行语句(code_rank, {'date': day})

    idx = 0
    for data in ts_data:
        data['index'] = idx
        data['key'] = date_str + '|' + data['股票代码']
        data['score'] = 0
        data['score3'] = 0
        data['score4'] = 0
        data['score5'] = 0
        data['score6'] = 0
        data['score7'] = 0
        idx += 1

    rank3 = ts_data.copy()
    rank3.sort(key=lambda x: x['3日涨幅'], reverse=True)

    rk = 1
    for rank in rank3[:num]:
        idx = rank['index']
        ts_data[idx]['score3'] = 1 - (rk - 1) / num
        ts_data[idx]['score'] += 1 - (rk - 1) / num
        rk = rk + 1

    rank4 = ts_data.copy()
    rank4.sort(key=lambda x: x['4日涨幅'], reverse=True)

    rk = 1
    for rank in rank4[:num]:
        idx = rank['index']
        ts_data[idx]['score4'] = 1 - (rk - 1) / num
        ts_data[idx]['score'] += 1 - (rk - 1) / num
        rk = rk + 1

    rank5 = ts_data.copy()
    rank5.sort(key=lambda x: x['5日涨幅'], reverse=True)

    rk = 1
    for rank in rank5[:num]:
        idx = rank['index']
        ts_data[idx]['score5'] = 1 - (rk - 1) / num
        ts_data[idx]['score'] += 1 - (rk - 1) / num
        rk = rk + 1

    rank6 = ts_data.copy()
    rank6.sort(key=lambda x: x['6日涨幅'], reverse=True)

    rk = 1
    for rank in rank6[:num]:
        idx = rank['index']
        ts_data[idx]['score6'] = 1 - (rk - 1) / num
        ts_data[idx]['score'] += 1 - (rk - 1) / num
        rk = rk + 1

    rank7 = ts_data.copy()
    rank7.sort(key=lambda x: x['7日涨幅'], reverse=True)

    rk = 1
    for rank in rank7[:num]:
        idx = rank['index']
        ts_data[idx]['score7'] = 1 - (rk - 1) / num
        ts_data[idx]['score'] += 1 - (rk - 1) / num
        rk = rk + 1

    ts_data.sort(key=lambda x: x['score'], reverse=True)
    ts_stocks = list()

    for data in ts_data:
        if data['score'] == 0:
            continue

        pkje = pc.get(data['key'])
        if not pkje:
            continue

        sell = sc.get(data['key'])
        if not sell:
            print('drop key:' + data['key'])
            continue

        data['竞价涨幅'] = pkje['竞价涨幅']
        data['买一价'] = pkje['买一价']
        data['盘口金额'] = pkje['盘口金额']
        data['早盘跌停盘口比'] = pkje['早盘跌停盘口比']
        data['卖出价'] = sell['sell_price']
        data['卖出日期'] = sell['sell_day']
        ts_stocks.append(data)

    for sort_key, head in [('score3', '3日'), ('score4', '4日'), ('score5', '5日'), ('score6', '6日'), ('score7', '7日'),
                           ('score', '总打分')]:
        count_earings(ts_stocks, sort_key, head)
    return ts_stocks


def count_earings(stock_data, sort_key, head):
    left_money = 3000 * 10000
    rank_stock_data = stock_data.copy()
    rank_stock_data.sort(key=lambda x: x[sort_key], reverse=True)

    for data in rank_stock_data:
        if data['盘口金额'] < 200 or data['竞价涨幅'] > 7 or data['早盘跌停盘口比'] > 1.1:
            continue

        if data['股票代码'][2:5] == '688':
            lots_mod = 200
        else:
            lots_mod = 100

        # 先按盘口金额的10%和开盘价买，手数要按100手和200手对齐
        use_money = data['盘口金额'] * 0.1 * 10000

        # 剩的钱不够盘口金额的10%了，有多少买多少
        if use_money > left_money:
            use_money = left_money

        buy_price = data['开盘价']
        buy_lots = use_money // buy_price
        buy_lots = buy_lots // lots_mod * lots_mod

        # 不足100或者200手的钱，就放弃这个股票，看下一个
        if buy_lots == 0:
            continue

        use_money = round(buy_lots * buy_price)
        real_use_money = use_money * 1.00022  # 手续费+印花税

        # 加了印花税和手续费后，可能不够钱买了，跳过
        if real_use_money > left_money:
            continue

        left_money -= real_use_money
        data[head + '买入金额'] = use_money
        real_sell_money = buy_lots * data['卖出价'] * (1 - 0.00012)
        data[head + '盈亏比'] = (real_sell_money / real_use_money - 1) * 100
        data[head + '盈亏金额'] = round(real_sell_money - real_use_money)


def get_dates(day):
    code = F读取脚本文件("dates.js")
    return F执行语句(code, {'day': day})


class pkje_cache(object):
    def __init__(self, code_file_name, csv_file_name):
        self.cache = dict()
        self.code = F读取脚本文件(code_file_name)
        self.csv_file_name = work_dir + csv_file_name
        self.fieldnames = ['key', '竞价涨幅', '买一价', '盘口金额', '早盘跌停盘口比']
        self.fd = None
        self.writer = None

    def build_cache(self):
        if not os.path.exists(self.csv_file_name):
            return False

        with open(self.csv_file_name, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row['key'] in self.cache:
                    print('重复key(%s) in pkje_cache' % row['key'])
                    return False

                if row['竞价涨幅'] == 'N/A':
                    self.cache[row['key']] = None
                    continue

                jjzf = float(row['竞价涨幅'])
                myj = float(row['买一价'])
                pkje = float(row['盘口金额'])
                zpdtpkb = float(row['早盘跌停盘口比'])
                self.cache[row['key']] = {'竞价涨幅': jjzf, '买一价': myj, '盘口金额': pkje, '早盘跌停盘口比': zpdtpkb}

        return True

    def get(self, key):
        if key in self.cache:
            return self.cache[key]

        key_ = key.split('|')
        if len(key_) != 2:
            return None

        print('downloading key %s' % key)
        day = key_[0]
        stock = key_[1]
        ret_data = F执行语句(self.code, {'day_': F生成天软日期_str(day), 'stockcode_': stock[2:]})

        if not self.fd:
            new_file = not os.path.exists(self.csv_file_name)
            self.fd = open(self.csv_file_name, mode='a', newline='')
            self.writer = csv.DictWriter(self.fd, fieldnames=self.fieldnames)
            if new_file:
                self.writer.writeheader()

        if not ret_data:
            data = {
                'key': key,
                '竞价涨幅': 'N/A'
            }
            self.cache[key] = None
        else:
            data = {
                'key': key,
                '竞价涨幅': ret_data[0]['竞价涨幅'],
                '买一价': ret_data[0]['买一价'],
                '盘口金额': ret_data[0]['盘口金额'],
                '早盘跌停盘口比': ret_data[0]['早盘跌停盘口比']
            }
            self.cache[key] = ret_data[0]

        self.writer.writerow(data)
        return self.cache[key]

    def __del__(self):
        if self.fd:
            self.fd.close()


class sell_cache(object):
    def __init__(self, selled_csv_file_name, not_selled_csv_file_name):
        self.cache = dict()
        self.selled_csv_file_name = work_dir + selled_csv_file_name
        self.not_selled_csv_file_name = work_dir + not_selled_csv_file_name

    def build_cache(self):
        if not os.path.exists(self.selled_csv_file_name):
            print("卖出文件未找到")
            return False

        if not os.path.exists(self.not_selled_csv_file_name):
            print("未卖出文件未找到")
            return False

        for csv_file_name in [self.selled_csv_file_name, self.not_selled_csv_file_name]:
            with open(csv_file_name, mode='r', newline='') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    key = row['key']
                    if key in self.cache:
                        print('重复key(%s) in sell_cache' % row['key'])
                        return False

                    sell_price = row['卖出价']
                    sell_day = row['卖出日期']
                    self.cache[key] = {
                        '卖出价': float(sell_price),
                        '卖出日期': sell_day
                    }

        return True

    def get(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            return None


def 运行打分策略():
    pc = pkje_cache("pankoujine.js", "pankoujine.csv")
    if not pc.build_cache():
        return

    sc = sell_cache('卖出明细30.csv', '卖出明细30_未完全卖出.csv')
    if not sc.build_cache():
        return

    ret_date = get_dates(20220602)

    ts_dates = [date['date'] for date in ret_date]
    date_key = dict()
    for date in ret_date:
        date_key[date['date']] = date['datestr']

    date_stocks = list()
    for date in ts_dates:
        print("counting ", date)
        sub_data_stocks = count_one_day_score(date, 150, pc, sc, date_key[date])
        date_stocks = date_stocks + sub_data_stocks

    with open(work_dir + '股票日期列表.csv', mode='w', newline='') as csv_file:
        fieldnames = ['key', '日期', '代码', '名称',
                      '买入价', '卖出价', '卖出日期',
                      '3日涨幅', '3日打分', '3日买入金额', '3日盈亏金额', '3日盈亏比',
                      '4日涨幅', '4日打分', '4日买入金额', '4日盈亏金额', '4日盈亏比',
                      '5日涨幅', '5日打分', '5日买入金额', '5日盈亏金额', '5日盈亏比',
                      '6日涨幅', '6日打分', '6日买入金额', '6日盈亏金额', '6日盈亏比',
                      '7日涨幅', '7日打分', '7日买入金额', '7日盈亏金额', '7日盈亏比',
                      '总打分', '总打分买入金额', '总打分盈亏金额', '总打分盈亏比',
                      '竞价涨幅', '买一价', '盘口金额', '早盘跌停盘口比',
                      ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for date_stock in date_stocks:
            row_data = {'key': date_stock['key'],
                        '日期': date_stock['key'].split('|')[0],
                        '代码': date_stock['key'].split('|')[1],
                        '名称': date_stock['股票名称'],
                        '买入价': '%.4f' % date_stock['开盘价'],
                        '卖出价': '%.4f' % date_stock['卖出价'],
                        '卖出日期': date_stock['卖出日期'],
                        '3日涨幅': '%.4f' % date_stock['3日涨幅'],
                        '3日打分': '%.4f' % date_stock['score3'],
                        '4日涨幅': '%.4f' % date_stock['4日涨幅'],
                        '4日打分': '%.4f' % date_stock['score4'],
                        '5日涨幅': '%.4f' % date_stock['5日涨幅'],
                        '5日打分': '%.4f' % date_stock['score5'],
                        '6日涨幅': '%.4f' % date_stock['6日涨幅'],
                        '6日打分': '%.4f' % date_stock['score6'],
                        '7日涨幅': '%.4f' % date_stock['7日涨幅'],
                        '7日打分': '%.4f' % date_stock['score7'],
                        '总打分': '%.4f' % date_stock['score'],
                        '竞价涨幅': '%.4f' % date_stock['竞价涨幅'],
                        '买一价': '%.4f' % date_stock['买一价'],
                        '盘口金额': '%.4f' % date_stock['盘口金额'],
                        '早盘跌停盘口比': '%.4f' % date_stock['早盘跌停盘口比'],
                        }
            for head in ['3日', '4日', '5日', '6日', '7日', '总打分']:
                if head + '盈亏金额' in date_stock:
                    row_data[head + '盈亏金额'] = date_stock[head + '盈亏金额']
                    row_data[head + '盈亏比'] = '%.4f' % date_stock[head + '盈亏比']
                    row_data[head + '买入金额'] = date_stock[head + '买入金额']
            writer.writerow(row_data)


def draw():
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['axes.unicode_minus'] = False
    data = {'0602': [100, 30], '0603': [200, 50], '0604': [300, 15], '0605': [200, 88], '0606': [100, 40]}
    df = pd.DataFrame(data.values(), index=data.keys(), columns=['3日收益', '4日收益'])
    df.plot(rot=90)
    plt.show()


code_lianban = F读取脚本文件("lianban.js")


def count_one_day_连板(day, date_str):
    ts_data = F执行语句(code_lianban, {'day': day, 'num': 2, 'backtrace_num': 3})

    for data in ts_data:
        data['key'] = date_str + '|' + data['代码']

    return ts_data


def 运行连板策略():
    ret_date = get_dates(20220616)

    ts_dates = [date['date'] for date in ret_date]
    date_key = dict()
    for date in ret_date:
        date_key[date['date']] = date['datestr']

    date_stocks = list()
    for date in ts_dates:
        print("counting ", date)
        sub_data_stocks = count_one_day_连板(date, date_key[date])
        date_stocks = date_stocks + sub_data_stocks

    with open(work_dir + '连板股票池.csv', mode='w', newline='') as csv_file:
        fieldnames = ['key', '日期', '代码', '名称',
                      '昨日连板涨幅', '前日连板涨幅', '昨日涨幅', '7日平均涨幅',
                      '昨日成交量', '前N日平均成交量', '入选原因'
                      ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for date_stock in date_stocks:
            row_data = {'key': date_stock['key'],
                        '日期': date_stock['key'].split('|')[0],
                        '代码': date_stock['代码'],
                        '名称': date_stock['名称'],
                        '昨日连板涨幅': date_stock['昨日连板涨幅'],
                        '前日连板涨幅': date_stock['前日连板涨幅'],
                        '昨日涨幅': date_stock['昨日涨幅'],
                        '7日平均涨幅': date_stock['7日平均涨幅'],
                        '昨日成交量': date_stock['昨日成交量'],
                        '前N日平均成交量': date_stock['前N日平均成交量'],
                        '入选原因': date_stock['入选原因']
                        }
            writer.writerow(row_data)


class minute_cache(object):
    def __init__(self, minute_csv_file_name, fieldnames):
        self.cache = dict()
        self.minute_csv_file_name = work_dir + minute_csv_file_name
        self.fieldnames = fieldnames
        self.fd = None
        self.writer = None

    def build_cache(self):
        if not os.path.exists(self.minute_csv_file_name):
            return True

        with open(self.minute_csv_file_name, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                date = row['日期']
                if date not in self.cache:
                    self.cache[date] = list()
                self.cache[date].append(row)

        return True

    def get(self, day, date_str):
        if date_str in self.cache:
            for data in self.cache[date_str]:
                data['day'] = day
            return self.cache[date_str]
        else:
            ret = count_one_day_分钟线(day, date_str)
            if not self.fd:
                new_file = not os.path.exists(self.minute_csv_file_name)
                self.fd = open(self.minute_csv_file_name, mode='a', newline='')
                self.writer = csv.DictWriter(self.fd, fieldnames=self.fieldnames)
                if new_file:
                    self.writer.writeheader()

            for row in ret:
                self.writer.writerow(row)
            return ret

    def __del__(self):
        if self.fd:
            self.fd.close()


code_fenzhongxian = F读取脚本文件("fenzhongxian.js")


def count_one_day_分钟线(day, date_str):
    ts_data = F执行语句(code_fenzhongxian, {'day': day})

    for data in ts_data:
        data['key'] = date_str + '|' + data['代码']
        data['日期'] = date_str
        data['day'] = day

    return ts_data


class buy_cache(object):
    def __init__(self, buy_csv_file_name):
        self.cache = dict()
        self.buy_csv_file_name = work_dir + buy_csv_file_name
        self.fieldnames = ['key', '买入价', '买入量']
        self.code = F读取脚本文件("fenzhongxianmairu.js")
        self.fd = None
        self.writer = None

    def build_cache(self):
        if not os.path.exists(self.buy_csv_file_name):
            return True

        with open(self.buy_csv_file_name, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                key = row['key']
                if key in self.cache:
                    print('重复key(%s) in buy_cache' % row['key'])
                    return False

                self.cache[key] = row
        return True

    def get(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            key_ = key.split('|')
            if len(key_) != 2:
                return None

            day = key_[0]
            stock = key_[1]
            ret_data = F执行语句(self.code, {'day': F生成天软日期_str(day), 'stock_code': stock[2:]})

            if not self.fd:
                new_file = not os.path.exists(self.buy_csv_file_name)
                self.fd = open(self.buy_csv_file_name, mode='a', newline='')
                self.writer = csv.DictWriter(self.fd, fieldnames=self.fieldnames)
                if new_file:
                    self.writer.writeheader()

            data = {'key': key, '买入价': ret_data[0], '买入量': int(ret_data[1])}
            self.writer.writerow(data)
            self.cache[key] = data
            return self.cache[key]

    def __del__(self):
        if self.fd:
            self.fd.close()


def count_earings_分钟线(date_stock, sc, bc):
    key = date_stock['key']

    date_stock['买入价'] = 0
    date_stock['买入量'] = 0
    date_stock['卖出价'] = 0
    date_stock['卖出日期'] = 0
    date_stock['买入金额'] = 0
    date_stock['盈亏金额'] = 0
    date_stock['盈亏比'] = 0

    sell_ret = sc.get(key)
    if not sell_ret:
        print("key %s 找不到卖出价" % key)
        return

    buy_ret = bc.get(key)
    if not buy_ret:
        print('key %s 计算买入失败' % key)
        return

    date_stock['买入价'] = float(buy_ret['买入价'])
    date_stock['买入量'] = int(buy_ret['买入量'])
    date_stock['卖出价'] = sell_ret['卖出价']
    date_stock['卖出日期'] = sell_ret['卖出日期']

    if date_stock['代码'][2:5] == '688':
        lots_mod = 200
    else:
        lots_mod = 100

    buy_price = date_stock['买入价']
    buy_lots = date_stock['买入量'] // lots_mod * lots_mod

    # 不足100或者200手的量，就放弃这个股票，看下一个
    if buy_lots == 0:
        return

    use_money = round(buy_lots * buy_price)
    real_use_money = round(use_money * 1.00012)  # 手续费+印花税

    date_stock['买入金额'] = use_money
    real_sell_money = buy_lots * date_stock['卖出价'] * (1 - 0.00022)
    date_stock['盈亏比'] = round((real_sell_money / real_use_money - 1) * 100, 2)
    date_stock['盈亏金额'] = round(real_sell_money - real_use_money)


def 运行分钟线策略():
    fieldnames = ['key', '日期', '代码', '名称',
                  '最高价涨幅', '最后均价涨幅', '最后收盘价涨幅',
                  '白线过3%分钟数', '白线高于黄线分钟数',
                  '买入量', '买入价', '卖出价', '卖出日期',
                  '买入金额', '盈亏金额', '盈亏比'
                  ]

    mc = minute_cache("分钟线股票池.csv", fieldnames)
    mc.build_cache()

    sc = sell_cache('卖出明细30.csv', '卖出明细30_未完全卖出.csv')
    if not sc.build_cache():
        return

    bc = buy_cache("买入明细.csv")
    if not bc.build_cache():
        return

    ret_date = get_dates(20220617)

    ts_dates = [date['date'] for date in ret_date]
    date_key = dict()
    for date in ret_date:
        date_key[date['date']] = date['datestr']

    date_stocks = list()
    for date in ts_dates:
        print("counting ", date)
        sub_data_stocks = mc.get(date, date_key[date])
        date_stocks = date_stocks + sub_data_stocks

    with open(work_dir + '分钟线策略.csv', mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for date_stock in date_stocks:
            count_earings_分钟线(date_stock, sc, bc)

            row_data = dict()
            for field in fieldnames:
                row_data[field] = date_stock[field]
            writer.writerow(row_data)


if __name__ == '__main__':
    F断开服务器()
    F连接服务器(b配置文件=True)
    运行分钟线策略()