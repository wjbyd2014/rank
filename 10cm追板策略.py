import csv_cache
from strategy import *
from functools import cmp_to_key


class Strategy10cm(Strategy):
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

    def post_count_buy_amount(self, data_list):
        for data in data_list:
            data['计划买入金额'] = 500 * 10000

    def select_stocks(self, data_list):
        for data in data_list:
            data['淘汰原因'] = ''

            if data['2日涨停数'] == 2:
                data['淘汰原因'] = '2连板'
                continue
            elif data['2日涨停数'] == 0:
                if data['30日涨停数'] == 0:  # 2天内没板，只要过去30天还有板，就行
                    data['淘汰原因'] = '没有远端涨停板'
                    continue
            else:
                assert data['2日涨停数'] == 1
                if data['5日涨停数'] > 1:  # 2天内有一个板，则5天内不能还有其他板了
                    data['淘汰原因'] = '没有远端涨停板'
                    continue
                elif data['30日涨停数'] == 1:  # 5天内没板，只要过去30天还有板，就行
                    data['淘汰原因'] = '没有远端涨停板'
                    continue

            max_buy_price_incr_ratio = self.cm.get_config_value('最大15日买入价涨幅')
            if max_buy_price_incr_ratio and data['买入价涨幅15'] > max_buy_price_incr_ratio:
                data['淘汰原因'] = '买入价涨幅'
                continue

            max_10day_two_vol = self.cm.get_config_value('最小10日最大两个天量之和')
            if max_10day_two_vol and data['10日最大两个天量之和'] < max_10day_two_vol:
                data['淘汰原因'] = '10日最大两个天量之和'
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
    zhuiban_strategy = Strategy10cm('10cm追板策略',
                                    'D:\\ts\\',
                                    ['当日排名', '淘汰原因'],
                                    '追板策略股票池.csv',
                                    {'日期': str, '代码': str, '名称': str,
                                     '买入价': float, '买入时间': str, '买入量': float,
                                     '1日涨停数': int, '2日涨停数': int, '3日涨停数': int, '4日涨停数': int,
                                     '5日涨停数': int, '6日涨停数': int, '7日涨停数': int,
                                     '10日涨停数': int, '15日涨停数': int, '30日涨停数': int,
                                     '买入价涨幅3': float, '买入价涨幅5': float, '买入价涨幅7': float,
                                     '买入价涨幅10': float, '买入价涨幅15': float, '买入价涨幅30': float,
                                     '买入价涨幅60': float, '上涨起点日': str
                                     },
                                    'zhuiban.js',
                                    {},
                                    None, None, None, None,
                                    ['日期', '代码', '名称', '可买金额', '盈亏金额', '盈亏比', '计划买入金额', '实际买入金额', '实际盈亏金额',
                                     '买入价', '卖出价', '当日排名', '淘汰原因'],
                                    ['买入量', '卖出日期'], 20220812, 800)

    zhuiban_strategy.set_data_filter(lambda data: data['代码'][2:4] in ['60', '00'])
    zhuiban_strategy.set_sort_data_list(sort_data_list)

    zhuiban_strategy.init()
    zhuiban_strategy.load_data()
    zhuiban_strategy.add_factor2('每日资金总量', [3000])
    zhuiban_strategy.add_factor2('单只股票购买上限', [3000])
    zhuiban_strategy.add_factor2('买入比', [100])
    zhuiban_strategy.add_factor2('尾部资金', [1])
    zhuiban_strategy.add_factor2('最大15日买入价涨幅', [6])
    zhuiban_strategy.gen_factors()

    len_factors = zhuiban_strategy.len_factors()
    print(f'len_factors = {len_factors}')

    if zhuiban_strategy.len_factors() == 1:
        zhuiban_strategy.run_in_normal_mode()
    elif zhuiban_strategy.len_factors() <= 20:
        zhuiban_strategy.run_in_linspace_compare_mode()
    else:
        zhuiban_strategy.run_in_linspace_count_mode(False)
