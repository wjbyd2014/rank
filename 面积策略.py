import csv
from functools import cmp_to_key
from config_manager import ConfigManager
from tinysoft import TinySoft
from csv_cache import ReadOnlyCsvCache
from csv_cache import ReadWriteDateCsvCache
from strategy_utils import *

work_dir = "D:\\ts\\"
ts = TinySoft(work_dir)
ts.F断开服务器()
ts.F连接服务器(b配置文件=False)

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
    use_money_per_stock = cm.get_config_value('每只股票最大购买金额') * 10000
    for data in data_list:
        data['买入价'] = data['买入时间'] = data['可买金额'] = data['计划买入金额'] = data['盈亏金额'] = data['盈亏比'] = 0

        """if data['观察期结束直接买入价'] != 0:
            data['买入价'] = data['观察期结束直接买入价']
            data['买入时间'] = '09:52:00'
        if data['大回撤买入价'] != 0:
            if data['买入价'] == 0 or data['大回撤结束时间'] < data['买入时间']:
                data['买入价'] = data['大回撤买入价']
                data['买入时间'] = data['大回撤结束时间']"""

        if data['双波谷买入价'] != 0 and data['观察期收盘价涨幅'] - data['双波谷涨幅'] < cm.get_config_value('购买时最大跌幅'):
            if data['买入价'] == 0 or data['双波谷触发时间'] < data['买入时间']:
                data['买入价'] = data['双波谷买入价']
                data['买入时间'] = data['双波谷触发时间']

        if data['买入价'] != 0:
            data['买入价'] *= 1.002
            data['可买金额'] = round(data['买入价'] * data['买入量'])
            data['计划买入金额'] = data['可买金额'] * (cm.get_config_value('买入比') / 100)

            if data['计划买入金额'] > use_money_per_stock:
                data['计划买入金额'] = use_money_per_stock

            data['盈亏比'] = round((data['卖出价'] / data['买入价'] - 1) * 100, 2)
            data['盈亏金额'] = round((data['卖出价'] - data['买入价']) * data['买入量'])

    data_list.sort(key=cmp_to_key(com_buy_price), reverse=True)

def count_stock_area_earn_money(data_list, writer):
    ret = 0
    left_money = 每日资金量 * 10000
    min_use_money_per_stock = cm.get_config_value('每只股票最小购买金额') * 10000

    for data in data_list:
        if data['买入价'] != 0 and left_money > 0:
            if data['计划买入金额'] > left_money:
                data['实际买入金额'] = left_money
            else:
                data['实际买入金额'] = data['计划买入金额']

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
    stock_per_day = cm.get_config_value('每日股票池数')
    for data in data_list:
        data['打分'] = data['面积']

        if data['1日涨停板数'] > 0:
            data['打分'] += cm.get_config_value('涨停板数1打分')
        elif data['3日涨停板数'] > 0:
            data['打分'] += cm.get_config_value('涨停板数3打分')
        elif data['5日涨停板数'] > 0:
            data['打分'] += cm.get_config_value('涨停板数5打分')
        elif data['7日涨停板数'] > 0:
            data['打分'] += cm.get_config_value('涨停板数7打分')

        if data['ma30向上'] == 0:
            data['打分'] -= cm.get_config_value('ma30打分')

        if data['上市天数'] < cm.get_config_value('最小上市天数'):
            data['打分'] = 0
            continue

        if data['观察期收盘价涨幅'] < cm.get_config_value('观察期收盘价涨幅'):
            data['打分'] = 0
            continue

        if data['量比'] < cm.get_config_value('最小量比'):
            data['打分'] = 0
            continue

        if data['双波谷前开板次数'] > cm.get_config_value('最大开板数量'):
            data['打分'] = 0
            continue

        if data['双波谷前开板次数'] > 0 and data['双波谷前最大开板回撤'] > cm.get_config_value('开板最大回撤'):
            data['打分'] = 0
            continue

    data_list.sort(key=lambda x: x['打分'], reverse=True)
    for data in data_list[:stock_per_day]:
        data['打分'] = round(data['打分'], 2)
        data_list2.append(data)


每日资金量 = 6000

cm = ConfigManager(work_dir + '回测.txt')
cm.add_factor1('每日股票池数', 100, 100, 10)
cm.add_factor1('购买时最大跌幅', 2.4, 2.4, 0.1)
cm.add_factor1('ma30打分', 0, 0, 5)
cm.add_factor1('涨停板数1打分', 86.5, 86.5, 0.5)
cm.add_factor1('涨停板数3打分', 220, 220, 0.5)
cm.add_factor1('涨停板数5打分', 115.5, 115.5, 0.5)
cm.add_factor1('涨停板数7打分', 0, 0, 1)
cm.add_factor1('观察期收盘价涨幅', -0.9, -0.9, 0.1)
cm.add_factor1('最小上市天数', 35, 35, 1)
cm.add_factor1('最小量比', 5.5, 5.5, 0.5)
cm.add_factor1('每只股票最大购买金额', 3600, 3600, 100)
cm.add_factor1('每只股票最小购买金额', 170, 170, 10)
cm.add_factor1('买入比', 50, 50, 1)
cm.add_factor1('最大开板数量', 8, 8, 1)
cm.add_factor1('开板最大回撤', 7.5, 7.5, 0.5)


def 运行面积策略(回测模式):
    len_list_factors = cm.len_factors()
    print('len_list_factors = ', len_list_factors)
    list_factors = cm.gen_factors()

    ac = ReadWriteDateCsvCache('area_cache', work_dir,
                               {'日期': str, '代码': str, '名称': str, '量比': float, '上市天数': int, '买入量': float,
                                '1日涨停板数': int, '3日涨停板数': int, '5日涨停板数': int, '7日涨停板数': int,
                                '是否涨停': int, '观察期收盘价涨幅': float, 'ma30向上': int,
                                '交叉点': str, '面积': float,
                                '观察期结束可以直接买入': int, '观察期结束直接买入价': float,
                                '大回撤开始时间': str, '大回撤结束时间': str, '大回撤买入价': float,
                                '上一波谷形成时间': str, '双波谷触发时间': str, '双波谷买入价': float, '双波谷涨幅': float,
                                '双波谷前开板次数': int, '双波谷前最大开板回撤': float},
                               ts,
                               'mianji.js', {'time1': '09:33:00', 'time2': '09:52:00', 'num': 800},
                               '面积策略股票池.csv'
                               )
    ac.build_cache()

    sc = ReadOnlyCsvCache('sell_cache', work_dir,
                          {'卖出价': float, '卖出日期': str},
                          ['卖出明细30.csv', '卖出明细30_未完全卖出.csv'])
    if not sc.build_cache():
        return

    if 回测模式:
        fd = None
        writer = None
    else:
        fd = open(work_dir + '面积策略.csv', mode='w', newline='')
        field_names = ['key'] + list(ac.fields_dict.keys()) + ['打分', '买入时间', '买入价', '卖出价', '卖出日期', '可买金额',
                                                               '盈亏金额', '盈亏比', '计划买入金额', '实际买入金额', '实际盈亏金额']
        writer = csv.DictWriter(fd, fieldnames=field_names)
        writer.writeheader()

    ret_date = ts.get_dates(20220718)
    ret_date.reverse()

    ts_dates = [date['date'] for date in ret_date]
    date_key = dict()
    for date in ret_date:
        date_key[date['date']] = date['datestr']

    max_total_earn_money = 0
    best_factors = None
    date_to_stock_data = dict()

    num = 0
    for factors in list_factors:
        num += 1
        total_earn_money = 0
        cm.update_configs(factors)

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

        '''
        print(
            '{}/{} '
            '每日股票池数({}) '
            '购买时最大跌幅({}) '
            'ma30打分({}) '
            '涨停板数1打分({:.1f}) '
            '涨停板数3打分({}) '
            '涨停板数5打分({}) '
            '涨停板数7打分({}) '
            '观察期收盘价涨幅({}) '
            '最小上市天数({}) '
            '最小量比({}) '
            '每只股票最大购买金额({}) '
            '每只股票最小购买金额({}) '
            '买入比({}) 最大开板数量({}) 开板最大回撤({}) 最大收益({})'.format(
                num, len_list_factors,
                cm.get_config_value('每日股票池数'),
                cm.get_config_value('购买时最大跌幅'),
                cm.get_config_value('ma30打分'),
                cm.get_config_value('涨停板数1打分'),
                cm.get_config_value('涨停板数3打分'),
                cm.get_config_value('涨停板数5打分'),
                cm.get_config_value('涨停板数7打分'),
                cm.get_config_value('观察期收盘价涨幅'),
                cm.get_config_value('最小上市天数'),
                cm.get_config_value('最小量比'),
                cm.get_config_value('每只股票最大购买金额'),
                cm.get_config_value('每只股票最小购买金额'),
                cm.get_config_value('买入比'),
                cm.get_config_value('最大开板数量'),
                cm.get_config_value('开板最大回撤'),
                max_total_earn_money)
        )
        '''

        if total_earn_money >= max_total_earn_money:
            max_total_earn_money = total_earn_money
            best_factors = factors
            cm.log(max_total_earn_money)

        if num % 100 == 0:
            print("num = ", num, ' 当前最大收益 = ', max_total_earn_money)

        if not 回测模式:
            draw_earn_money(earn_money, work_dir, '面积策略收益图', False)

    if not 回测模式:
        fd.close()
    print('best_factors = ', best_factors)
    print('max_total_earn_money = ', round(max_total_earn_money))


if __name__ == '__main__':
    运行面积策略(False)
