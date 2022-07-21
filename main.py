import json
import os
import re
import sys
import csv
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
    def __init__(self, csv_file_name, time1, time2, num):
        self.cache = dict()
        self.time1 = time1
        self.time2 = time2
        self.num = num
        self.csv_file_name = csv_file_name
        self.field_names = ['key', '日期', '代码', '名称', '量比',
                            '上市天数', '买入量', '1日涨停板数', '3日涨停板数', '5日涨停板数', '7日涨停板数',
                            '是否涨停', '观察期收盘价涨幅', 'ma30向上',
                            '交叉点', '面积',
                            '观察期结束可以直接买入', '观察期结束直接买入价', '大回撤开始时间', '大回撤结束时间', '大回撤买入价',
                            '上一波谷形成时间', '双波谷触发时间', '双波谷买入价', '双波谷涨幅']
        self.convert_field_names = {'量比': float,
                                    '上市天数': int, '买入量': float, '是否涨停': int, '观察期收盘价涨幅': float,
                                    '面积': float, 'ma30向上': int,
                                    '观察期结束可以直接买入': int, '观察期结束直接买入价': float, '大回撤买入价': float,
                                    '双波谷买入价': float, '双波谷涨幅': float,
                                    '1日涨停板数': int, '3日涨停板数': int, '5日涨停板数': int, '7日涨停板数': int}

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
                            {'day': key, 'time1': self.time1, 'time2': self.time2, 'num': self.num})

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


def 分箱(min_value, max_value, interval):
    ret = list()
    value = min_value
    while value <= max_value:
        ret.append(value)
        value += interval
    return ret


def gen_factors(list_params):
    if len(list_params) == 1:
        for param in list_params[0]:
            yield [param]
    else:
        list_factor = gen_factors(list_params[1:])
        for factor in list_factor:
            for param in list_params[0]:
                yield [param] + factor


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
    use_money_per_stock = 每只股票最大购买金额 * 10000
    for data in data_list:
        data['买入价'] = data['买入时间'] = data['可买金额'] = data['买入金额'] = data['盈亏金额'] = data['盈亏比'] = 0

        """if data['观察期结束直接买入价'] != 0:
            data['买入价'] = data['观察期结束直接买入价']
            data['买入时间'] = '09:52:00'
        if data['大回撤买入价'] != 0:
            if data['买入价'] == 0 or data['大回撤结束时间'] < data['买入时间']:
                data['买入价'] = data['大回撤买入价']
                data['买入时间'] = data['大回撤结束时间']"""

        if data['双波谷买入价'] != 0 and data['观察期收盘价涨幅'] - data['双波谷涨幅'] < 购买时最大跌幅:
            if data['买入价'] == 0 or data['双波谷触发时间'] < data['买入时间']:
                data['买入价'] = data['双波谷买入价']
                data['买入时间'] = data['双波谷触发时间']

        if data['买入价'] != 0:
            data['买入价'] *= 1.002
            data['可买金额'] = round(data['买入价'] * data['买入量'])
            data['买入金额'] = data['可买金额'] * (买入比 / 100)

            if data['买入金额'] > use_money_per_stock:
                data['买入金额'] = use_money_per_stock

            data['盈亏比'] = round((data['卖出价'] / data['买入价'] - 1) * 100, 2)
            data['盈亏金额'] = round((data['卖出价'] - data['买入价']) * data['买入量'])

    data_list.sort(key=cmp_to_key(com_buy_price), reverse=True)

上交所手续费 = 0#0.00013
深交所手续费 = 0#0.00011
印花税 = 0#0.001
def count_stock_area_earn_money(data_list, writer):
    ret = 0
    left_money = 每日资金量 * 10000
    min_use_money_per_stock = 每只股票最小购买金额 * 10000

    for data in data_list:
        if data['买入价'] != 0 and left_money > 0:
            if data['买入金额'] > left_money:
                data['实际买入金额'] = left_money
            else:
                data['实际买入金额'] = data['买入金额']

            if data['代码'][0:2] == 'SH':
                手续费 = 上交所手续费
            else:
                手续费 = 深交所手续费
            实际买入量 = int(data['实际买入金额'] / data['买入价'])
            data['实际买入金额'] = data['买入价'] * 实际买入量
            实际使用资金 = data['实际买入金额'] * (1 + 手续费)
            left_money -= 实际使用资金
            data['实际盈亏金额'] = 实际买入量 * data['卖出价'] * (1 - 手续费 - 印花税) - 实际使用资金
            ret += data['实际盈亏金额']
            if left_money < min_use_money_per_stock:
                left_money = 0
        else:
            data['实际买入金额'] = data['实际盈亏金额'] = 0

        if writer:
            data['买入价'] = round(data['买入价'], 3)
            data['实际买入金额'] = round(data['实际买入金额'])
            data['实际盈亏金额'] = round(data['实际盈亏金额'])
            writer.writerow(data)
    return ret, left_money


def select_stocks(data_list, data_list2):
    stock_per_day = 每日股票池数
    for data in data_list:
        data['打分'] = data['面积']

        if data['1日涨停板数'] > 0:
            data['打分'] += 涨停板数1打分
        elif data['3日涨停板数'] > 0:
            # data['打分'] += 涨停板数3打分 * (data['3日涨停板数'] - data['1日涨停板数'])
            data['打分'] += 涨停板数3打分
        elif data['5日涨停板数'] > 0:
            # data['打分'] += 涨停板数5打分 * (data['5日涨停板数'] - data['3日涨停板数'])
            data['打分'] += 涨停板数5打分
        elif data['7日涨停板数'] > 0:
            # data['打分'] += 涨停板数7打分 * (data['7日涨停板数'] - data['7日涨停板数'])
            data['打分'] += 涨停板数7打分

        if data['ma30向上'] == 0:
            data['打分'] -= ma30打分

        if data['上市天数'] < 最小上市天数:
            data['打分'] = 0

        if data['观察期收盘价涨幅'] < 观察期收盘价涨幅:
            data['打分'] = 0

        if data['量比'] < 最小量比:
            data['打分'] = 0

    data_list.sort(key=lambda x: x['打分'], reverse=True)
    for data in data_list[:stock_per_day]:
        data['打分'] = round(data['打分'], 2)
        data_list2.append(data)


每日资金量 = 6000

每日股票池数 = 100
购买时最大跌幅 = 10
涨停板数1打分 = 500
涨停板数3打分 = 250
涨停板数5打分 = 100
涨停板数7打分 = 50
ma30打分 = 50
观察期收盘价涨幅 = -5
最小上市天数 = 0
最小量比 = 0
每只股票最大购买金额 = 1800
每只股票最小购买金额 = 100
买入比 = 100


def 运行面积策略(回测模式):
    global 每日股票池数, 购买时最大跌幅, ma30打分, 涨停板数1打分, 涨停板数3打分, 涨停板数5打分, 涨停板数7打分, 观察期收盘价涨幅, 最小上市天数, 最小量比, 每只股票最大购买金额, 每只股票最小购买金额, 买入比

    每日股票池数因子 = 分箱(100, 100, 10)
    购买时最大跌幅因子 = 分箱(2, 2, 0.1)
    ma30打分因子 = 分箱(0, 0, 5)
    涨停板数1打分因子 = 分箱(90, 90, 10)
    涨停板数3打分因子 = 分箱(190, 190, 10)
    涨停板数5打分因子 = 分箱(110, 110, 5)
    涨停板数7打分因子 = 分箱(1, 1, 1)
    观察期收盘价涨幅因子 = 分箱(-0.9, -0.9, 0.1)
    最小上市天数因子 = 分箱(35, 35, 1)
    最小量比因子 = 分箱(5.5, 5.5, 0.5)
    每只股票最大购买金额因子 = 分箱(1800, 1800, 100)
    每只股票最小购买金额因子 = 分箱(170, 170, 10)
    买入比因子 = 分箱(100, 100, 1)

    len_list_factors = 1
    len_list_factors *= len(每日股票池数因子)
    len_list_factors *= len(购买时最大跌幅因子)
    len_list_factors *= len(ma30打分因子)
    len_list_factors *= len(涨停板数1打分因子)
    len_list_factors *= len(涨停板数3打分因子)
    len_list_factors *= len(涨停板数5打分因子)
    len_list_factors *= len(涨停板数7打分因子)
    len_list_factors *= len(观察期收盘价涨幅因子)
    len_list_factors *= len(最小上市天数因子)
    len_list_factors *= len(最小量比因子)
    len_list_factors *= len(每只股票最大购买金额因子)
    len_list_factors *= len(每只股票最小购买金额因子)
    len_list_factors *= len(买入比因子)

    list_factors = gen_factors([每日股票池数因子, 购买时最大跌幅因子, ma30打分因子,
                                涨停板数1打分因子, 涨停板数3打分因子, 涨停板数5打分因子, 涨停板数7打分因子, 观察期收盘价涨幅因子,
                                最小上市天数因子, 最小量比因子, 每只股票最大购买金额因子, 每只股票最小购买金额因子, 买入比因子
                                ])

    ac = area_cache(work_dir + '面积策略股票池.csv', '09:33:00', '09:52:00', 800)
    ac.build_cache()

    sc = sell_cache('卖出明细30.csv', '卖出明细30_未完全卖出.csv')
    if not sc.build_cache():
        return

    if 回测模式:
        fd = None
        writer = None
    else:
        fd = open(work_dir + '面积策略.csv', mode='w', newline='')
        writer = csv.DictWriter(fd, fieldnames=ac.field_names + ['打分', '买入时间', '买入价', '卖出价', '卖出日期', '可买金额', '买入金额',
                                                                 '盈亏金额', '盈亏比', '实际买入金额', '实际盈亏金额'])
        writer.writeheader()

    ret_date = get_dates(20220718)
    ret_date.reverse()

    ts_dates = [date['date'] for date in ret_date]
    date_key = dict()
    for date in ret_date:
        date_key[date['date']] = date['datestr']

    max_total_earn_money = 0
    best_factors = None
    date_to_stock_data = dict()

    file_result = open(work_dir + '回测.txt', 'w')
    num = 0
    for factors in list_factors:
        num += 1
        total_earn_money = 0
        每日股票池数, 购买时最大跌幅, ma30打分, 涨停板数1打分, 涨停板数3打分, 涨停板数5打分, 涨停板数7打分, 观察期收盘价涨幅, 最小上市天数, 最小量比, 每只股票最大购买金额, 每只股票最小购买金额, 买入比 = factors

        earn_money = dict()
        for date in ts_dates:
            if not 回测模式:
                print('counting ', date)

            if num == 1:
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
                date_to_stock_data[date] = data_list

            data_list2 = list()
            select_stocks(date_to_stock_data[date], data_list2)
            select_buy_price(data_list2)
            got_money, left_money = count_stock_area_earn_money(data_list2, writer)
            if left_money > 0:
                print("%s left %d\n" % (date, left_money))
            earn_money[date] = got_money
            total_earn_money += got_money

        file_result.write('%d %d %d %d %d %d %d %d %d %d %d %d %d %d\n' %
                          (每日股票池数, 购买时最大跌幅, ma30打分, 涨停板数1打分, 涨停板数3打分, 涨停板数5打分, 涨停板数7打分, 观察期收盘价涨幅,
                           最小上市天数, 最小量比, 每只股票最大购买金额, 每只股票最小购买金额, 买入比, total_earn_money))
        print(
            '%d/%d 每日股票池数(%d) 购买时最大跌幅(%d) ma30打分(%d) 涨停板数1打分(%d) 涨停板数3打分(%d) 涨停板数5打分(%d) 涨停板数7打分(%d) 观察期收盘价涨幅(%d) 最小上市天数(%d) 最小量比(%d) 每只股票最大购买金额(%d) 每只股票最小购买金额(%d) 买入比(%d) 最大收益(%d)' %
            (num, len_list_factors, 每日股票池数, 购买时最大跌幅, ma30打分,
             涨停板数1打分, 涨停板数3打分, 涨停板数5打分, 涨停板数7打分, 观察期收盘价涨幅,
             最小上市天数, 最小量比, 每只股票最大购买金额, 每只股票最小购买金额, 买入比, max_total_earn_money))
        if num % 100 == 0:
            file_result.flush()

        if total_earn_money > max_total_earn_money:
            max_total_earn_money = total_earn_money
            best_factors = factors

        if not 回测模式:
            draw_earn_money(earn_money, work_dir, '面积策略收益图', False)

    if not 回测模式:
        fd.close()
    print('best_factors = ', best_factors)
    print('max_total_earn_money = ', round(max_total_earn_money))


if __name__ == '__main__':
    F断开服务器()
    F连接服务器(b配置文件=False)
    运行面积策略(False)
