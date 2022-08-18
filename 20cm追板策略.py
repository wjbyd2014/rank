import csv_cache
from strategy import *
from functools import cmp_to_key


class Strategy20cm(Strategy):
    def __init__(self, name, work_dir, csv_field_names,
                 stock_pool_file_name, stock_pool_fields, stock_pool_js_file_name, stock_pool_js_params,
                 stock_info_file_name, stock_info_fields, stock_info_js_file_name, stock_info_js_params,
                 priority_fields, skipped_csv_fields, begin_date, date_num):
        super().__init__(name, work_dir, csv_field_names,
                         stock_pool_file_name, stock_pool_fields, stock_pool_js_file_name, stock_pool_js_params,
                         stock_info_file_name, stock_info_fields, stock_info_js_file_name, stock_info_js_params,
                         priority_fields, skipped_csv_fields, begin_date, date_num)

    def __del__(self):
        super().__del__()

    def select_stocks(self, data_list):
        for data in data_list:
            data['淘汰原因'] = ''

            range_kai_pan_jia = self.cm.get_config_value('开盘价涨幅范围')
            if range_kai_pan_jia:
                price_pair = range_kai_pan_jia.split('~')

                if not float(price_pair[0]) <= data['开盘价涨幅'] <= float(price_pair[1]):
                    data['淘汰原因'] = '开盘价涨幅'

            if data['连扳数'] < 2 and data['100日内出现5日涨幅超70'] == 1:
                data['淘汰原因'] = '100日内出现5日涨幅超70'
                continue


def com_function(data1, data2):
    if data1.get('淘汰原因'):
        return 1
    if data2.get('淘汰原因'):
        return -1
    else:
        if data1['买入时间'] < data2['买入时间']:
            return -1
        elif data1['买入时间'] == data2['买入时间']:
            return 0
        else:
            return 1


def sort_data_list(data_list):
    data_list.sort(key=cmp_to_key(com_function))


if __name__ == '__main__':
    zhuiban_strategy = Strategy20cm('20cm追板策略',
                                    'D:\\ts\\',
                                    ['当日排名', '淘汰原因'],
                                    '追板策略股票池.csv',
                                    {'日期': str, '代码': str, '名称': str,
                                     '买入价': float, '买入时间': str, '买入量': float, '当日已成交金额': float,
                                     '买入价涨幅3': float, '买入价涨幅5': float, '买入价涨幅7': float,
                                     '买入价涨幅10': float, '买入价涨幅15': float, '买入价涨幅30': float,
                                     '1日涨停数': int, '2日涨停数': int, '3日涨停数': int, '4日涨停数': int,
                                     '5日涨停数': int, '6日涨停数': int, '7日涨停数': int,
                                     '10日涨停数': int, '15日涨停数': int, '30日涨停数': int,
                                     '100日内出现5日涨幅超70': int,
                                     '200日内出现5日涨幅超70': int,
                                     '100日首板新高': int
                                     },
                                    'zhuiban.js',
                                    {},
                                    '每日股票信息.csv',
                                    {'名称': str, '代码': str, '上市天数': float, 'ma3向上': int, 'ma5向上': int,
                                     '开盘价涨停': int, '开盘价涨幅': float, '昨日是否一字板': int,
                                     '连扳数': int, '10日最大两个天量之和': float,
                                     '昨天缩量大涨': int, '前天缩量大涨': int
                                     },
                                    'stock_info_day.js',
                                    {},
                                    ['日期', '代码', '名称', '可买金额', '盈亏金额', '盈亏比', '计划买入金额', '实际买入金额', '实际盈亏金额',
                                     '开盘价涨停', '100日首板新高', '当日已成交金额', '昨天缩量大涨', '前天缩量大涨', '连扳数', '当日排名', '淘汰原因'],
                                    ['买入量', '卖出日期'], 20220727, 300)

    zhuiban_strategy.add_factor2('尾部资金', [1])
    zhuiban_strategy.add_factor2('最大连扳数', [1])
    zhuiban_strategy.set_max_use_money_per_day(3000)
    zhuiban_strategy.set_data_filter(lambda data: data['代码'][2:4] not in ['60', '00'])
    zhuiban_strategy.set_sort_data_list(sort_data_list)

    len_factors = zhuiban_strategy.len_factors()
    print(f'len_factors = {len_factors}')

    zhuiban_strategy.init()
    zhuiban_strategy.load_data()
    factors = ConfigManager.linspace2(zhuiban_strategy.get_data(), '开盘价涨幅', 10)
    zhuiban_strategy.add_factor2('开盘价涨幅范围', factors)

    zhuiban_strategy.gen_factors()

    if zhuiban_strategy.len_factors() == 1:
        zhuiban_strategy.run_in_normal_mode()
    elif zhuiban_strategy.len_factors() <= 20:
        zhuiban_strategy.run_in_linspace_compare_mode()
    else:
        zhuiban_strategy.run_in_linspace_count_mode(False)
