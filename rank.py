# -*- coding: utf-8 -*-
import json
import sys
import csv

sys.path.append("D:\Tinysoft\Analyse.NET")
import TSLPy3 as ts


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


def F读取脚本文件(filename):
    with open("D:\\" + filename, 'r', encoding='utf-8') as f:
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


def count_one_day(day, num):
    code = F读取脚本文件("rank.js")
    ts_data = F执行语句(code, {'date': day})
    # print(ts_data)

    idx = 0
    for data in ts_data:
        data['index'] = idx
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
    ts_stocks = [(day, data['股票代码'], data['股票名称'],
                  data['score3'], data['score4'], data['score5'], data['score6'], data['score7'], data['score'],
                  data['3日涨幅'], data['4日涨幅'], data['5日涨幅'], data['6日涨幅'], data['7日涨幅']
                  ) for data in ts_data if data['score'] > 0]
    return ts_stocks


def get_dates(day):
    code = F读取脚本文件("dates.js")
    return F执行语句(code, {'day': day})


if __name__ == '__main__':
    F断开服务器()
    F连接服务器(b配置文件=True)

    ret_date = get_dates(20220602)

    ts_dates = [date['date'] for date in ret_date]
    date_key = dict()
    for date in ret_date:
        date_key[date['date']] = date['datestr']

    date_stocks = list()
    for date in ts_dates:
        print("counting ", date)
        sub_data_stocks = count_one_day(date, 150)
        date_stocks = date_stocks + sub_data_stocks

    with open('D://股票日期列表.csv', mode='w', newline='') as csv_file:
        fieldnames = ['key', '日期', '股票代码', '股票名称',
                      '3日涨幅', '3日打分',
                      '4日涨幅', '4日打分',
                      '5日涨幅', '5日打分',
                      '6日涨幅', '6日打分',
                      '7日涨幅', '7日打分',
                      '综合打分']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for date_stock in date_stocks:
            date_str = date_key[date_stock[0]]
            writer.writerow({'key': date_str + '|' + date_stock[1],
                             '日期': date_str,
                             '股票代码': date_stock[1],
                             '股票名称': date_stock[2],
                             '3日涨幅': '%.4f' % date_stock[9],
                             '3日打分': '%.4f' % date_stock[3],
                             '4日涨幅': '%.4f' % date_stock[10],
                             '4日打分': '%.4f' % date_stock[4],
                             '5日涨幅': '%.4f' % date_stock[11],
                             '5日打分': '%.4f' % date_stock[5],
                             '6日涨幅': '%.4f' % date_stock[12],
                             '6日打分': '%.4f' % date_stock[6],
                             '7日涨幅': '%.4f' % date_stock[13],
                             '7日打分': '%.4f' % date_stock[7],
                             '综合打分': '%.4f' % date_stock[8]})
