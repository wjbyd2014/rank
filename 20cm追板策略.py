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
            data['可买金额'] = data['原始金额'] * 1.5
            data['原始金额'] = round(data['原始金额'] / 10000)

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
        max_ztls = self.cm.get_config_value('涨停拉升')
        min_ztls_check_rank = self.cm.get_config_value('涨停拉升最小排名')

        if not max_buy_rank or max_buy_rank == -1:
            return

        for rank, data in enumerate(data_list):
            if data['2日涨停数'] == 0 and data['5日涨停数'] != 0:
                data['淘汰原因'] = '涨停中断'
            elif rank + 1 > min_ztls_check_rank and data['涨停拉升'] > max_ztls:
                data['淘汰原因'] = '涨停拉升'
            elif rank + 1 > max_buy_rank:
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
                                     '买入价': float, '买入时间': str, '原始金额': float, '当日已成交金额': float,
                                     '2日涨停数': int, '3日涨停数': int, '4日涨停数': int, '5日涨停数': int, '次日下午成交额': float,
                                     '涨停拉升': float, 'ma5上涨起始日': str, '本轮上涨幅度': float, '本轮上涨涨停板个数': int, '连扳数': int
                                     },
                                    'zhuiban.js',
                                    {},
                                    '', {}, '', {},
                                    ['日期', '代码', '名称',
                                     '原始金额', '可买金额', '盈亏比',
                                     '计划买入金额', '计划买入盈亏金额',
                                     '实际买入金额', '实际盈亏金额',
                                     '是否买入', '当日排名', '淘汰原因',
                                     '买入时间', '买入价', '卖出价', '卖出日期'],
                                    ['买入量'], 20221211, 850)

    zhuiban_strategy.set_sort_data_list(zhuiban_strategy.sort_data_list_by_time)

    zhuiban_strategy.init()
    zhuiban_strategy.load_data()
    """factors = ConfigManager.linspace2(zhuiban_strategy.get_data(), '开盘价涨幅', 10)
    zhuiban_strategy.add_factor2('开盘价涨幅范围', factors)"""
    zhuiban_strategy.add_factor2('每日资金总量', [3000])
    zhuiban_strategy.add_factor2('单只股票购买上限', [3000])
    # zhuiban_strategy.add_factor2('单只股票购买下限', [200])
    zhuiban_strategy.add_factor2('买入比', [100])
    zhuiban_strategy.add_factor2('尾部资金', [1])

    zhuiban_strategy.add_factor2('买入排名上限', [10])
    zhuiban_strategy.add_factor2('涨停拉升', [4])
    zhuiban_strategy.add_factor2('涨停拉升最小排名', [1])

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
