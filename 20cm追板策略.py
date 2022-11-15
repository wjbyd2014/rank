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

    def pre_count_buy_amount(self, data_list):
        for data in data_list:
            orig_money = data['原始金额']
            data['原始金额'] = int(data['原始金额'] / 10000)
            if data['原始金额'] < 1000:
                data['可买金额'] = 50 * 10000
            elif data['原始金额'] < 3000:
                data['可买金额'] = 100 * 10000
            elif data['原始金额'] < 6000:
                data['可买金额'] = 150 * 10000
            elif data['原始金额'] < 15000:
                data['可买金额'] = int(orig_money / 60)
            elif data['原始金额'] < 20000:
                data['可买金额'] = int(orig_money / 75)
            else:
                data['可买金额'] = int(orig_money / 90)

    """def select_stocks(self, data_list):
        for data in data_list:
            data['是否买入'] = 0
            data['淘汰原因'] = ''

            if data['3日涨停数'] == 0 and data['5日涨停数'] != 0:
                data['淘汰原因'] = '涨停中断'
                continue

            range_kai_pan_jia = self.cm.get_config_value('开盘价涨幅范围')
            if range_kai_pan_jia:
                price_pair = range_kai_pan_jia.split('~')

                if not float(price_pair[0]) <= data['开盘价涨幅'] <= float(price_pair[1]):
                    data['淘汰原因'] = '开盘价涨幅'"""

    def sort_data_list_by_time(self, data_list):
        # data_list.sort(key=cmp_to_key(com_function))
        data_list.sort(key=lambda x: x['买入时间'])
        max_buy_rank = self.cm.get_config_value('买入排名上限')

        if not max_buy_rank or max_buy_rank == -1:
            return

        for rank, data in enumerate(data_list):
            if rank + 1 <= 4:
                data['计划买入金额'] = data['计划买入金额'] * 1.2
                data['计划买入盈亏金额'] = data['盈亏比'] * data['计划买入金额'] / 100

            if data['2日涨停数'] == 0 and data['5日涨停数'] != 0:
                data['淘汰原因'] = '涨停中断'

            if rank + 1 > max_buy_rank:
                if not data['淘汰原因']:
                    data['淘汰原因'] = '买入排名'


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


if __name__ == '__main__':
    zhuiban_strategy = Strategy20cm('20cm追板策略',
                                    'D:\\ts\\',
                                    ['当日排名', '淘汰原因'],
                                    '追板策略股票池.csv',
                                    {'日期': str, '代码': str, '名称': str,
                                     '买入价': float, '买入时间': str, '原始金额': float, '原始金额2': float, '当日已成交金额': float,
                                     '2日涨停数': int, '3日涨停数': int, '4日涨停数': int, '5日涨停数': int, '次日下午成交额': float,
                                     '涨停拉升': float, 'ma5上涨起始日': str, '本轮上涨幅度': float, '本轮上涨涨停板个数': int
                                     },
                                    'zhuiban.js',
                                    {},
                                    '每日股票信息.csv',
                                    {
                                        '连扳数': int
                                    },
                                    'stock_info_day.js',
                                    {},
                                    ['日期', '代码', '名称',
                                     '原始金额', '原始金额2', '可买金额', '盈亏比',
                                     '计划买入金额', '计划买入盈亏金额',
                                     '实际买入金额', '实际盈亏金额',
                                     '是否买入', '当日排名', '淘汰原因',
                                     '买入时间', '买入价', '卖出价', '卖出日期'],
                                    ['买入量', '备注'], 20221108, 850)

    zhuiban_strategy.set_data_filter(lambda data: data['代码'][2:4] not in ['60', '00'])
    zhuiban_strategy.set_sort_data_list(zhuiban_strategy.sort_data_list_by_time)

    zhuiban_strategy.init()
    zhuiban_strategy.load_data()
    """factors = ConfigManager.linspace2(zhuiban_strategy.get_data(), '开盘价涨幅', 10)
    zhuiban_strategy.add_factor2('开盘价涨幅范围', factors)"""
    zhuiban_strategy.add_factor2('每日资金总量', [2500])
    zhuiban_strategy.add_factor2('单只股票购买上限', [750])
    # zhuiban_strategy.add_factor2('单只股票购买下限', [200])
    zhuiban_strategy.add_factor2('买入比', [100])
    zhuiban_strategy.add_factor2('尾部资金', [1])

    zhuiban_strategy.add_factor2('买入排名上限', [10])
    # zhuiban_strategy.add_factor2('涨停板买入量放大系数', [1])
    # zhuiban_strategy.add_factor2('实际买入量缩小系数', [60])
    zhuiban_strategy.gen_factors()

    len_factors = zhuiban_strategy.len_factors()
    print(f'len_factors = {len_factors}')

    if zhuiban_strategy.len_factors() == 1:
        zhuiban_strategy.run_in_normal_mode()
    elif zhuiban_strategy.len_factors() <= 20:
        zhuiban_strategy.run_in_linspace_compare_mode()
    else:
        zhuiban_strategy.run_in_linspace_count_mode(False)
