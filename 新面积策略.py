from config_manager import ConfigManager
from csv_cache import *
from strategy_utils import *
from tinysoft import TinySoft

work_dir = "D:\\ts\\"
ts = TinySoft(work_dir)
ts.F断开服务器()
ts.F连接服务器(b配置文件=False)


def count_buy_amount(data_list):
    use_money_per_stock = cm.get_config_value('每只股票最大购买金额') * 10000
    for data in data_list:
        data['可买金额'] = data['计划买入金额'] = data['盈亏金额'] = data['盈亏比'] = 0

        assert (data['买入价'] > 0)

        if data['买入量'] > 0:
            data['可买金额'] = round(data['买入价'] * data['买入量'])
            data['计划买入金额'] = data['可买金额'] * (cm.get_config_value('买入比') / 100)

            if data['计划买入金额'] > use_money_per_stock:
                data['计划买入金额'] = use_money_per_stock

            data['盈亏比'] = round((data['卖出价'] / data['买入价'] - 1) * 100, 2)
            data['盈亏金额'] = round((data['卖出价'] - data['买入价']) * data['买入量'])


def count_stock_area_earn_money(data_list, writer, 回测模式):
    ret = 0
    use_money = 0
    left_money = 每日资金量 * 10000
    min_use_money_per_stock = cm.get_config_value('每只股票最小购买金额') * 10000

    for data in data_list:
        if left_money > 0:
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
            use_money += 实际使用资金
            left_money -= 实际使用资金
            data['实际盈亏金额'] = 实际买入量 * data['卖出价'] * (1 - 手续费 - 印花税) - 实际使用资金
            ret += data['实际盈亏金额']
            if left_money < min_use_money_per_stock:
                left_money = 0
        else:
            data['实际买入金额'] = data['实际盈亏金额'] = 0

            if 回测模式:
                break

        if not 回测模式:
            data['买入价'] = round(data['买入价'], 3)
            data['实际买入金额'] = round(data['实际买入金额'])
            data['实际盈亏金额'] = round(data['实际盈亏金额'])
            writer.writerow(data)
    return ret, use_money, left_money


def select_stocks(data_list):
    for data in data_list:
        data['打分'] = data['平均面积']

        if data['1日涨停板数'] > 0:
            data['打分'] += cm.get_config_value('涨停板数1打分')
        if data['3日涨停板数'] > 0:
            data['打分'] += cm.get_config_value('涨停板数3打分') * (data['3日涨停板数'] - data['1日涨停板数'])
        if data['5日涨停板数'] > 0:
            data['打分'] += cm.get_config_value('涨停板数5打分') * (data['5日涨停板数'] - data['3日涨停板数'])
        if data['7日涨停板数'] > 0:
            data['打分'] += cm.get_config_value('涨停板数7打分') * (data['7日涨停板数'] - data['5日涨停板数'])

        data['打分'] += cm.get_config_value('最低点系数') * data['最低点']
        data['打分'] += cm.get_config_value('最高点系数') * data['最高点']

        if data['观察期结束是否涨停'] == 1:
            data['打分'] = 0
            continue

        if data['买入量'] == 0:
            data['打分'] = 0
            continue

        if data['量比'] < cm.get_config_value('最小量比'):
            data['打分'] = 0
            continue

        if data['开板次数'] > cm.get_config_value('最大开板次数'):
            data['打分'] = 0
            continue

        if data['开板最大回撤'] > cm.get_config_value('最大开板最大回撤'):
            data['打分'] = 0
            continue

        if data['上市天数'] < cm.get_config_value('最小上市天数'):
            data['打分'] = 0
            continue

        if data['涨板打断次数'] > cm.get_config_value('最大断板次数'):
            data['打分'] = 0
            continue

    data_list.sort(key=lambda x: x['打分'], reverse=True)


每日资金量 = 6000

cm = ConfigManager(work_dir + '回测.txt')
cm.add_factor1('涨停板数1打分', 3.7, 3.7, 0.1)
cm.add_factor1('涨停板数3打分', 1.6, 1.6, 0.1)
cm.add_factor1('涨停板数5打分', 1.4, 1.4, 0.1)
cm.add_factor1('涨停板数7打分', 5.8, 5.8, 0.1)
cm.add_factor1('最小上市天数', 200, 200, 1)
cm.add_factor1('最小量比', 0.3, 0.3, 0.1)
cm.add_factor1('每只股票最大购买金额', 1800, 1800, 100)
cm.add_factor1('每只股票最小购买金额', 100, 100, 10)
cm.add_factor1('买入比', 100, 100, 1)
cm.add_factor1('最大开板次数', 4, 4, 1)
cm.add_factor1('最大开板最大回撤', 14.0, 14.0, 0.1)
cm.add_factor1('最高点系数', 0.59, 0.59, 0.01)
cm.add_factor1('最低点系数', 0.44, 0.44, 0.01)
cm.add_factor1('最大断板次数', 2, 2, 1)


def 运行新面积策略(回测模式):
    len_list_factors = cm.len_factors()
    print('len_list_factors = ', len_list_factors)
    list_factors = cm.gen_factors()

    stock_poll_cache = ReadWriteDateCsvCache('stock_poll_cache', work_dir,
                                             {'日期': str, '代码': str, '名称': str, '量比': float,
                                              '买入量': float, '买入价': float, '观察期结束是否涨停': int,
                                              '交叉点': str, '总面积': float, '平均面积': float,
                                              '1日涨停板数': int, '3日涨停板数': int, '5日涨停板数': int, '7日涨停板数': int,
                                              '开板次数': int, '开板最大回撤': float, '最高点': float, '最低点': float
                                              }, ts, 'mianji_stock_poll.js',
                                             {'time1': '09:33:00', 'time2': '09:53:00',
                                              'time3': '09:54:00', 'time4': '09:58:00', 'num': 800},
                                             '新面积策略股票池.csv')
    stock_poll_cache.build_cache()

    stock_info_cache = ReadWriteKeyCsvCache('stock_info_cache', work_dir,
                                            {'上市天数': int, 'ma3向上': int, 'ma5向上': int,
                                             '上涨起点日': str, '涨板打断次数': int
                                             }, ts, 'mianji_stock_info.js',
                                            {}, '新面积策略股票信息.csv')
    stock_info_cache.build_cache()

    sell_cache = ReadOnlyCsvCache('sell_cache', work_dir,
                                  {'卖出价': float, '卖出日期': str},
                                  ['卖出明细30.csv', '卖出明细30_未完全卖出.csv'])
    sell_cache.build_cache()

    if 回测模式:
        fd = None
        writer = None
    else:
        fd = open(work_dir + '新面积策略.csv', mode='w', newline='')
        field_names = ['key'] + stock_poll_cache.keys() + stock_info_cache.keys() + \
                      ['打分', '卖出价', '卖出日期', '可买金额',
                       '盈亏金额', '盈亏比', '计划买入金额', '实际买入金额',
                       '实际盈亏金额']

        writer = csv.DictWriter(fd, fieldnames=field_names)
        writer.writeheader()

    ret_date = ts.get_dates(20220727)
    ret_date.reverse()

    ts_dates = [date['date'] for date in ret_date]
    date_key = dict()
    for date in ret_date:
        date_key[date['date']] = date['datestr']

    max_earn_money_ratio = 0
    max_earn_money = 0
    best_factors = None
    date_to_stock_data = dict()

    num = 0
    for factors in list_factors:
        num += 1
        total_earn_money = 0
        total_use_money = 0
        cm.update_configs(factors)

        earn_money = dict()
        for date in ts_dates:
            if not 回测模式:
                print('counting ', date)

            if num == 1:
                stock_data = stock_poll_cache.get(date, date_key[date])
                if not stock_data:
                    print("计算个股面积失败, date = ", date)
                    return

                data_list = list()
                for data in stock_data:
                    stock_info = stock_info_cache.get(data['key'])
                    if not stock_info:
                        print("get stock info failed, key = ", data['key'])
                        continue

                    for key in stock_info_cache.keys():
                        data[key] = stock_info[key]

                    sell_info = sell_cache.get(data['key'])
                    if not sell_info:
                        print("sell price not found, key = ", data['key'])
                        continue

                    data['卖出价'] = sell_info['卖出价']
                    data['卖出日期'] = sell_info['卖出日期']

                    data_list.append(data)
                count_buy_amount(data_list)
                date_to_stock_data[date] = data_list

            data_list_copy = date_to_stock_data[date].copy()
            select_stocks(data_list_copy)
            got_money, use_money, left_money = count_stock_area_earn_money(data_list_copy, writer, 回测模式)

            if left_money > 0:
                print(f"{date} left {left_money}\n")

            earn_money[date] = got_money
            total_earn_money += got_money
            total_use_money += use_money

        earn_money_ratio = total_earn_money * 10000 / total_use_money
        if earn_money_ratio > max_earn_money_ratio:
            max_earn_money = total_earn_money
            max_earn_money_ratio = earn_money_ratio
            best_factors = factors
            cm.log(max_earn_money_ratio)

        # cm.print(num, len_list_factors, max_earn_money_ratio)

        if num % 100 == 0:
            print("num = ", num, ' 当前最大收益 = ', max_earn_money_ratio)

        if not 回测模式:
            draw_earn_money(earn_money, work_dir, '新面积策略收益图', False)
            """earn_money2 = dict()
            for date, money in earn_money.items():
                earn_money2[date] = 0.8 * money
            earn_money3 = dict()
            for date, money in earn_money.items():
                earn_money3[date] = 1.2 * money
            draw_list_earn_money([earn_money, earn_money2, earn_money3], ['1','2','3'], work_dir, '新面积策略收益图', False)"""

    if not 回测模式:
        fd.close()

    print('best_factors = ', best_factors)
    print('max_earn_money_ratio = ', round(max_earn_money_ratio))
    print('max_earn_money = ', max_earn_money)


if __name__ == '__main__':
    运行新面积策略(True)
