import json
import os
import re
import sys
import csv
import math
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from functools import cmp_to_key

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
            return True

        if not os.path.exists(self.not_selled_csv_file_name):
            print("未卖出文件未找到")
            return True

        for csv_file_name in [self.selled_csv_file_name, self.not_selled_csv_file_name]:
            with open(csv_file_name, mode='r', newline='') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    key = row['key']
                    if key in self.cache and self.cache[key]['卖出价'] != float(row['卖出价']):
                        print('重复key(%s) in sell_cache, 而且卖出价不一致' % row['key'])
                        continue

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


class factor_cache:
    def __init__(self, csv_file_name):
        self.cache = dict()
        self.csv_file_name = work_dir + csv_file_name

    def build_cache(self):
        if not os.path.exists(self.csv_file_name):
            print("factor文件未找到")
            return False

        with open(self.csv_file_name, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                key = row['key']
                if key in self.cache:
                    print('重复key(%s) in factor_cache' % row['key'])
                    continue

                self.cache[key] = {
                    'f1': float(row['f1']),
                    'f2': float(row['f2']),
                    'f3': float(row['f3']),
                    'f4': float(row['f4'])
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

    return ts_data


class buy_cache(object):
    def __init__(self, buy_csv_file_name):
        self.cache = dict()
        self.buy_csv_file_name = work_dir + buy_csv_file_name
        self.fieldnames = ['key', '买入价', '买入量', '昨日涨停', '前日涨停']
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

            print("计算分钟线买入，key = %s" % key_)

            day = key_[0]
            stock = key_[1]
            ret_data = F执行语句(self.code, {'day': F生成天软日期_str(day), 'stock_code': stock[2:]})

            if not self.fd:
                new_file = not os.path.exists(self.buy_csv_file_name)
                self.fd = open(self.buy_csv_file_name, mode='a', newline='')
                self.writer = csv.DictWriter(self.fd, fieldnames=self.fieldnames)
                if new_file:
                    self.writer.writeheader()

            data = {'key': key, '买入价': ret_data[0], '买入量': int(ret_data[1]), '昨日涨停': ret_data[2], '前日涨停': ret_data[3]}
            self.writer.writerow(data)
            self.cache[key] = data
            return self.cache[key]

    def __del__(self):
        if self.fd:
            self.fd.close()


def count_earings_分钟线(date_stocks, date, sc, bc, fc):
    print("计算分钟线收益 ", date)
    for date_stock in date_stocks:
        key = date_stock['key']
        date_stock['买入价'] = 0
        date_stock['买入量'] = 0
        date_stock['卖出价'] = 0
        date_stock['卖出日期'] = 0
        date_stock['买入金额'] = 0
        date_stock['盈亏金额'] = 'N/A'
        date_stock['盈亏比'] = 0

        buy_ret = bc.get(key)
        if not buy_ret:
            print('key %s 计算买入失败' % key)
            return

        fc_ret = fc.get(key)
        if not fc_ret:
            print('key %s 读取因子失败' % key)
            return

        date_stock['f1'] = float(fc_ret['f1'])
        date_stock['f2'] = float(fc_ret['f2'])
        date_stock['f3'] = float(fc_ret['f3'])
        date_stock['f4'] = float(fc_ret['f4'])

        date_stock['买入价'] = float(buy_ret['买入价'])
        date_stock['买入量'] = int(buy_ret['买入量'])
        date_stock['昨日涨停'] = buy_ret['昨日涨停']
        date_stock['前日涨停'] = buy_ret['前日涨停']

        buy_price = date_stock['买入价']
        buy_lots = date_stock['买入量']
        date_stock['买入金额'] = math.ceil(buy_lots * buy_price)

        if buy_price == 0:
            continue

        sell_ret = sc.get(key)
        if not sell_ret:
            print("key %s 找不到卖出价" % key)
            continue

        date_stock['卖出价'] = sell_ret['卖出价']
        date_stock['卖出日期'] = sell_ret['卖出日期']
        date_stock['盈亏比'] = round((date_stock['卖出价'] / date_stock['买入价'] - 1) * 100, 2)

    date_stocks.sort(key=lambda x: x['f2'], reverse=True)

    left_money = 6000 * 10000
    max_use_money_per_stock = 1500 * 10000
    ret = 0

    for date_stock in date_stocks:
        should_return = False
        if date_stock['买入金额'] > max_use_money_per_stock:
            date_stock['买入量'] = int(max_use_money_per_stock / date_stock['买入价'])
            date_stock['买入金额'] = math.ceil(date_stock['买入量'] * date_stock['买入价'])

        if date_stock['买入金额'] > left_money:
            date_stock['买入量'] = int(left_money / date_stock['买入价'])

            if date_stock['买入量'] == 0:
                date_stock['买入金额'] = date_stock['买入量'] = 0
                return ret

            date_stock['买入金额'] = math.ceil(date_stock['买入量'] * date_stock['买入价'])
            should_return = True

        use_money = date_stock['买入金额']

        if use_money == 0:
            continue

        real_use_money = round(use_money * 1.00012)  # 手续费
        real_sell_money = date_stock['买入量'] * date_stock['卖出价'] * (1 - 0.00022)  # 手续费+印花税
        date_stock['盈亏比'] = round((real_sell_money / real_use_money - 1) * 100, 2)
        date_stock['盈亏金额'] = round(real_sell_money - real_use_money)
        ret += date_stock['盈亏金额']

        left_money -= use_money

        if should_return or left_money < 10000:
            return ret


def 运行分钟线策略():
    fieldnames = ['key', '日期', '代码', '名称',
                  '最高价涨幅', '最后均价涨幅', '最后收盘价涨幅',
                  '白线过3%分钟数', '白线高于黄线分钟数',
                  '买入量', '买入价', '卖出价', '卖出日期',
                  '买入金额', '盈亏金额', '盈亏比',
                  'f1', 'f2', 'f3', 'f4',
                  '昨日涨停', '前日涨停'
                  ]

    mc = minute_cache("分钟线股票池.csv", fieldnames)
    mc.build_cache()

    sc = sell_cache('卖出明细30.csv', '卖出明细30_未完全卖出.csv')
    if not sc.build_cache():
        return

    bc = buy_cache("买入明细.csv")
    if not bc.build_cache():
        return

    fc = buy_cache("临时因子.csv")
    if not fc.build_cache():
        return

    ret_date = get_dates(20220617)
    ret_date.reverse()

    ts_dates = [date['date'] for date in ret_date]
    date_key = dict()
    for date in ret_date:
        date_key[date['date']] = date['datestr']

    date_stocks = list()
    day_earn_money = dict()
    for date in ts_dates:
        print("counting ", date)
        sub_data_stocks = mc.get(date, date_key[date])
        ret = count_earings_分钟线(sub_data_stocks, date, sc, bc, fc)
        day_earn_money[int(date)] = ret
        date_stocks = date_stocks + sub_data_stocks

    with open(work_dir + '分钟线策略(f2从大到小).csv', mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for date_stock in date_stocks:
            row_data = dict()
            for field in fieldnames:
                row_data[field] = date_stock[field]
            writer.writerow(row_data)

    draw_earn_money(day_earn_money, '分钟线收益图')


class zz1000_withdraw_cache:
    def __init__(self, csv_file_name):
        self.cache = dict()
        self.csv_file_name = csv_file_name
        self.field_names = ['key', '最大回撤开始时间', '最大回撤结束时间', '最大跌幅持续时间', '最大跌幅百分比',
                            '最大反向回撤开始时间', '最大反向回撤结束时间', '最大反向回撤持续时间', '最大反向回撤百分比',
                            '次大反向回撤开始时间', '次大反向回撤结束时间', '次大反向回撤持续时间', '次大反向回撤百分比']
        self.code = F读取脚本文件("dapanhuiche.js")
        self.fd = None
        self.writer = None

    def build_cache(self):
        if not os.path.exists(self.csv_file_name):
            return

        with open(self.csv_file_name, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                key = row['key']
                if key in self.cache:
                    print('重复key(%s) in zz1000_withdraw_cache' % row['key'])
                    continue

                data = {}
                for field in self.field_names:
                    data[field] = row[field]
                self.cache[int(key)] = data

    def get(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            print("计算大盘回撤, date = ", key)
            ts_data = F执行语句(self.code, {'day': key})
            data = ts_data[0]
            data['key'] = key

            if not self.fd:
                new_file = not os.path.exists(self.csv_file_name)
                self.fd = open(self.csv_file_name, mode='a', newline='')
                self.writer = csv.DictWriter(self.fd, fieldnames=self.field_names)
                if new_file:
                    self.writer.writeheader()

            self.writer.writerow(data)
            self.cache[key] = data
            return data

    def __del__(self):
        if self.fd:
            self.fd.close()


class stock_withdraw_cache:
    def __init__(self, csv_file_name):
        self.cache = dict()
        self.csv_file_name = csv_file_name
        self.field_names = ['key', '日期', '代码', '名称', '量比',
                            '观察期开始', '观察期结束',
                            '开盘以来最高涨幅', '观察期最高涨幅', '观察期最低涨幅', '观察期起点', '观察期终点', '观察期涨幅',
                            '最大回撤开始时间', '最大回撤结束时间', '最大回撤持续时间', '最大回撤起点', '最大回撤终点', '最大回撤百分比',
                            '回撤结束后反弹最高点', '回撤结束后反弹百分比',
                            '上市天数', '买入价', '买入量']

        self.code = F读取脚本文件("geguhuiche.js")
        self.fd = None
        self.writer = None

    def build_cache(self):
        if not os.path.exists(self.csv_file_name):
            return

        with open(self.csv_file_name, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                key = row['key']
                key_ = key.split('|')
                if len(key_) != 2:
                    return None

                day = key_[0]
                one_day = re.split('[-/]', day)
                day = int(one_day[0]) * 10000 + int(one_day[1]) * 100 + int(one_day[2])
                data = {}
                for field in self.field_names:
                    data[field] = row[field]
                self.cache.setdefault(day, list())
                self.cache[day].append(data)

    def get(self, key, date_str, begin_time, end_time):
        if key in self.cache:
            return self.cache[key]
        else:
            print("计算个股回撤, key = ", key)
            ts_data = F执行语句(self.code, {'day': key, 'begin_time': begin_time, 'end_time': end_time})

            if not self.fd:
                new_file = not os.path.exists(self.csv_file_name)
                self.fd = open(self.csv_file_name, mode='a', newline='')
                self.writer = csv.DictWriter(self.fd, fieldnames=self.field_names)
                if new_file:
                    self.writer.writeheader()

            for data in ts_data:
                data['key'] = date_str + '|' + data['代码']
                data['日期'] = date_str
                data['回撤结束后反弹百分比'] = round(data['回撤结束后反弹最高点'] - data['观察期终点'], 3)
                self.writer.writerow(data)
            self.cache[key] = ts_data
            return ts_data

    def __del__(self):
        if self.fd:
            self.fd.close()


def count_stock_withdraw_buy_sell(data, sc_ret):
    buy_price = float(data['买入价'])
    buy_vol = float(data['买入量'])
    data['买入金额'] = buy_price * buy_vol
    sell_price = sc_ret['卖出价']
    sell_day = sc_ret['卖出日期']
    data['卖出价'] = sell_price
    data['卖出日期'] = sell_day
    use_money = buy_price * buy_vol
    sell_money = sell_price * buy_vol
    if use_money > 0:
        data['盈亏金额'] = round(sell_money - use_money)
        data['盈亏比'] = round((sell_money / use_money - 1) * 100, 2)
    else:
        data['盈亏金额'] = data['盈亏比'] = 0


def count_stock_withdraw_earn_money(data_list, writer):
    ret = 0
    left_money = 6000 * 10000
    max_use_money_per_stock = 1600 * 10000
    min_use_money_per_stock = 160 * 10000

    for data in data_list:
        if float(data['开盘以来最高涨幅']) < 2.5:
            continue

        if float(data['回撤结束后反弹最高点']) < 2:
            continue

        if float(data['买入量']) < 100:
            continue

        if int(data['上市天数']) < 5:
            continue

        if data['买入金额'] < min_use_money_per_stock:
            continue

        if left_money > 0:
            if data['买入金额'] > max_use_money_per_stock:
                data['实际买入金额'] = max_use_money_per_stock
            else:
                data['实际买入金额'] = data['买入金额']

            if data['实际买入金额'] > left_money:
                data['实际买入金额'] = left_money

            data['实际盈亏金额'] = round(data['实际买入金额'] * (float(data['卖出价']) / float(data['买入价']) - 1))
            ret += data['实际盈亏金额']
            left_money -= data['实际买入金额']

            if left_money < min_use_money_per_stock:
                left_money = 0
        else:
            data['实际买入金额'] = data['实际盈亏金额'] = 0

        writer.writerow(data)
    return ret


def 运行回撤趋势图策略():
    zwc = zz1000_withdraw_cache(work_dir + '大盘回撤.csv')
    zwc.build_cache()

    swc = stock_withdraw_cache(work_dir + '回撤股票池.csv')
    swc.build_cache()

    sc = sell_cache('卖出明细30.csv', '卖出明细30_未完全卖出.csv')
    if not sc.build_cache():
        return

    fd = open(work_dir + '回撤策略.csv', mode='w', newline='')
    writer = csv.DictWriter(fd, fieldnames=swc.field_names + ['买入金额', '卖出价', '卖出日期', '盈亏金额', '盈亏比', '实际买入金额', '实际盈亏金额'])
    writer.writeheader()

    ret_date = get_dates(20220701)
    ret_date.reverse()

    ts_dates = [date['date'] for date in ret_date]
    date_key = dict()
    earn_money = dict()
    for date in ret_date:
        date_key[date['date']] = date['datestr']

    for date in ts_dates:
        withdraw = zwc.get(date)
        if not withdraw:
            print("count withdraw failed, date = ", date)
        else:
            begin_time = withdraw['最大回撤开始时间']
            end_time = withdraw['最大回撤结束时间']

            stock_data = swc.get(date, date_key[date], begin_time, end_time)
            if not stock_data:
                print("计算个股回撤失败, date = ", date)
                return

            data_list = list()
            for data in stock_data:
                sc_ret = sc.get(data['key'])
                if not sc_ret:
                    print("sell price not found, key = ", data['key'])
                    continue

                count_stock_withdraw_buy_sell(data, sc_ret)
                data_list.append(data)

            data_list.sort(key=lambda x: float(x['回撤结束后反弹最高点']), reverse=True)
            ret = count_stock_withdraw_earn_money(data_list, writer)
            earn_money[date] = ret
    draw_earn_money(earn_money, work_dir, '回撤结束后反弹最高点(从大到小)', False)
    fd.close()


def draw_earn_money(day_earn_money, work_dir, title, show_picture):
    earn_money = 0
    d = dict()
    for day in day_earn_money:
        earn_money += day_earn_money[day]
        d[pd.to_datetime(str(day))] = [earn_money / 10000]

    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['axes.unicode_minus'] = False

    df = pd.DataFrame(d.values(), index=list(d.keys()), columns=['总收益'])
    ymax = df.max().max()
    ymin = df.min().min()
    xmax = df.index.max()
    xmin = df.index.min()

    ax1 = df.plot(figsize=(14, 6), yticks=[*np.linspace(ymin, ymax, 20)], rot=90, sharey=False,
                  subplots=False, grid=True, fontsize=8)

    alldays = matplotlib.dates.DayLocator(interval=5)  # 主刻度为每月
    ax1.xaxis.set_major_locator(alldays)  # 设置主刻度
    ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y%m%d'))  # 主刻度格式为年月日
    ax1.xaxis.set_minor_formatter(plt.NullFormatter())  # 取消副刻度
    ax1.set_xlim(xmin, xmax)  # x轴范围
    ax1.set_ylim(ymin, ymax)  # y轴范围
    plt.subplots_adjust(top=0.96, bottom=0.09, right=0.97, left=0.03, hspace=0.02, wspace=0.02)
    plt.title(title)
    if show_picture:
        plt.show()
    else:
        f = plt.gcf()  # 获取当前图像
        path = work_dir + '{}.png'.format(title)
        f.savefig(path)
    print("earn_money = ", earn_money)


class area_cache:
    def __init__(self, csv_file_name, time1, time2, time3, num):
        self.cache = dict()
        self.time1 = time1
        self.time2 = time2
        self.time3 = time3
        self.num = num
        self.csv_file_name = csv_file_name
        self.field_names = ['key', '日期', '代码', '名称', '量比',
                            '上市天数', '买入量', '1日涨停板数', '3日涨停板数', '5日涨停板数', '是否涨停', '收盘价涨幅', '交叉点', '面积',
                            '观察期结束可以直接买入', '观察期结束直接买入价', '大回撤开始时间', '大回撤结束时间', '大回撤买入价',
                            '上一波谷形成时间', '双波谷触发时间', '双波谷买入价']
        self.convert_field_names = {'量比': float,
                                    '上市天数': int, '买入量': float, '是否涨停': int, '收盘价涨幅': float, '面积': float,
                                    '观察期结束可以直接买入': int, '观察期结束直接买入价': float, '大回撤买入价': float, '双波谷买入价': float}

        self.code = F读取脚本文件("mianji.js")
        self.fd = None
        self.writer = None

    def build_cache(self):
        if not os.path.exists(self.csv_file_name):
            return

        with open(self.csv_file_name, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                key = row['key']
                key_ = key.split('|')
                if len(key_) != 2:
                    return None

                day = key_[0]
                one_day = re.split('[-/]', day)
                day = int(one_day[0]) * 10000 + int(one_day[1]) * 100 + int(one_day[2])
                data = {}
                for field in self.field_names:
                    data[field] = row[field]
                self.cache.setdefault(day, list())
                for field in self.convert_field_names:
                    data[field] = self.convert_field_names[field](data[field])
                self.cache[day].append(data)

    def get(self, key, date_str):
        if key in self.cache:
            return self.cache[key]
        else:
            ts_data = F执行语句(self.code,
                            {'day': key, 'time1': self.time1, 'time2': self.time2, 'time3': self.time3,
                             'num': self.num})

            if not self.fd:
                new_file = not os.path.exists(self.csv_file_name)
                self.fd = open(self.csv_file_name, mode='a', newline='')
                self.writer = csv.DictWriter(self.fd, fieldnames=self.field_names)
                if new_file:
                    self.writer.writeheader()

            for data in ts_data:
                data['key'] = date_str + '|' + data['代码']
                data['日期'] = date_str
                self.writer.writerow(data)
            self.cache[key] = ts_data
            return ts_data

    def __del__(self):
        if self.fd:
            self.fd.close()


def com_buy_price(data1, data2):
    if data1['买入价'] != 0 and data2['买入价'] != 0:
        if data1['买入时间'] < data2['买入时间']:
            return 1
        elif data1['买入时间'] > data2['买入时间']:
            return -1
        else:
            return 0
    else:
        if data1['买入价'] > data2['买入价']:
            return 1
        elif data1['买入价'] < data2['买入价']:
            return -1
        else:
            return 0


def select_buy_price(data_list):
    max_use_money_per_stock = 1800 * 10000
    for data in data_list:
        data['买入价'] = data['买入时间'] = data['可买金额'] = data['买入金额'] = data['盈亏金额'] = data['盈亏比'] = 0

        '''if data['观察期结束直接买入价'] != 0:
            data['买入价'] = data['观察期结束直接买入价']
            data['买入时间'] = '09:52:00'
        if data['大回撤买入价'] != 0:
            if data['买入价'] == 0 or data['大回撤结束时间'] < data['买入时间']:
                data['买入价'] = data['大回撤买入价']
                data['买入时间'] = data['大回撤结束时间']'''

        if data['双波谷买入价'] != 0:
            if data['买入价'] == 0 or data['双波谷触发时间'] < data['买入时间']:
                data['买入价'] = data['双波谷买入价']
                data['买入时间'] = data['双波谷触发时间']

        if data['买入价'] != 0:
            data['买入价'] *= 1.002
            data['可买金额'] = round(data['买入价'] * data['买入量'])
            data['买入金额'] = data['可买金额']

            if data['买入金额'] > max_use_money_per_stock:
                data['买入金额'] = max_use_money_per_stock

            data['盈亏比'] = round((data['卖出价'] / data['买入价'] - 1) * 100, 2)
            data['盈亏金额'] = round((data['卖出价'] - data['买入价']) * data['买入量'])

    data_list.sort(key=cmp_to_key(com_buy_price), reverse=True)


def count_stock_area_earn_money(data_list, writer):
    ret = 0
    left_money = 6000 * 10000
    min_use_money_per_stock = 100 * 10000

    for data in data_list:
        if data['买入价'] != 0 and left_money > 0:
            if data['买入金额'] > left_money:
                data['实际买入金额'] = left_money
            else:
                data['实际买入金额'] = data['买入金额']

            data['实际盈亏金额'] = round(data['实际买入金额'] * (data['卖出价'] / data['买入价'] - 1))
            ret += data['实际盈亏金额']
            left_money -= data['实际买入金额']

            if left_money < min_use_money_per_stock:
                left_money = 0
        else:
            data['实际买入金额'] = data['实际盈亏金额'] = 0

        writer.writerow(data)
    return ret, left_money


def select_stocks(data_list, data_list2):
    stock_per_day = 50
    for data in data_list:
        if data['是否涨停'] == 1:
            data_list2.append(data)
        elif stock_per_day > 0:
            data_list2.append(data)
            stock_per_day -= 1


def 运行面积策略():
    ac = area_cache(work_dir + '面积策略股票池.csv', '09:33:00', '09:52:00', '11:00:00', 800)
    ac.build_cache()

    sc = sell_cache('卖出明细30.csv', '卖出明细30_未完全卖出.csv')
    if not sc.build_cache():
        return

    fd = open(work_dir + '面积策略.csv', mode='w', newline='')
    writer = csv.DictWriter(fd, fieldnames=ac.field_names + ['买入时间', '买入价', '卖出价', '卖出日期', '可买金额', '买入金额',
                                                             '盈亏金额', '盈亏比', '实际买入金额', '实际盈亏金额'])
    writer.writeheader()

    ret_date = get_dates(20220718)
    ret_date.reverse()

    ts_dates = [date['date'] for date in ret_date]
    date_key = dict()
    for date in ret_date:
        date_key[date['date']] = date['datestr']

    earn_money = dict()
    for date in ts_dates:
        print('counting ', date)
        stock_data = ac.get(date, date_key[date])
        if not stock_data:
            print("计算个股面积失败, date = ", date)
            return

        data_list = list()
        for data in stock_data:
            sc_ret = sc.get(data['key'])
            if not sc_ret:
                print("sell price not found, key = ", data['key'])
                continue

            data['卖出价'] = sc_ret['卖出价']
            data['卖出日期'] = sc_ret['卖出日期']
            data_list.append(data)

        data_list2 = list()
        select_stocks(data_list, data_list2)
        select_buy_price(data_list2)
        got_money, left_money = count_stock_area_earn_money(data_list2, writer)
        if left_money > 0:
            print("%s left %d\n" % (date, left_money))
        earn_money[date] = got_money
    draw_earn_money(earn_money, work_dir, '面积策略收益图', False)
    fd.close()


if __name__ == '__main__':
    F断开服务器()
    F连接服务器(b配置文件=True)
    运行面积策略()
