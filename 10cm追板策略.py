import csv_cache
from strategy import *


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

    def select_stocks(self, data_list):
        for data in data_list:
            data['打分'] = 1
            pass

    def pre_process_data(self, data_list):
        pass

    def post_process_data(self, data_list):
        pass


if __name__ == '__main__':
    area_strategy = Strategy10cm('10cm追板策略',
                                 'D:\\ts\\',
                                 ['打分', '当日排名', '淘汰原因'],
                                 '10cm追板策略股票池.csv',
                                 {'日期': str, '代码': str, '名称': str,
                                  '买入价': float, '买入时间': str, '买入量': float,
                                  '1日涨停数': int, '2日涨停数': int, '3日涨停数': int, '5日涨停数': int,
                                  '7日涨停数': int, '10日涨停数': int, '15日涨停数': int, '30日涨停数': int,
                                  '3日最高价': float, '5日最高价': float, '7日最高价': float, '10日最高价': float,
                                  '15日最高价': float, '30日最高价': float,
                                  '3日涨幅': float, '5日涨幅': float, '7日涨幅': float
                                  },
                                 'zhuiban10cm.js',
                                 {},
                                 '每日股票信息.csv',
                                 {'名称': str, '代码': str, '上市天数': float, 'ma3向上': int, 'ma5向上': int,
                                  '上涨起点日': str, '涨板打断次数': int,
                                  '开盘价涨幅': float, '昨日是否一字板': int,
                                  '1日低位涨停板数': int, '3日低位涨停板数': int, '5日低位涨停板数': int,
                                  '7日低位涨停板数': int, '10日低位涨停板数': int,
                                  '10日阴线数': int, '3日十字阴线极值': float, '5日十字阴线极值': float, '10日十字阴线极值': float
                                  },
                                 'stock_info_day.js',
                                 {},
                                 ['日期', '代码', '名称', '可买金额', '盈亏金额', '盈亏比', '计划买入金额', '实际买入金额', '实际盈亏金额',
                                  '买入价', '卖出价', '打分', '当日排名'],
                                 ['买入量', '卖出日期'], 20220727, 300)

    area_strategy.add_factor2('尾部资金', [1])
    area_strategy.set_max_use_money_per_day(3000)
    area_strategy.set_data_filter(lambda data: data['代码'][2:4] in ['60', '00'])

    len_factors = area_strategy.len_factors()
    print(f'len_factors = {len_factors}')

    test_sell_cache = csv_cache.ReadWriteDateKeyCsvCache('test_sell_cache', area_strategy.work_dir,
                                                         {'代码': str, '名称': str, '卖出价': float, '卖出日期': str, '卖出时间': str},
                                                         area_strategy.ts, 'sell.js',
                                                         {'time': '13:55:00'},
                                                         'test_sell.csv')
    area_strategy.sell_cache = test_sell_cache
    area_strategy.init()

    if area_strategy.len_factors() == 1:
        area_strategy.run_in_normal_mode()
    elif area_strategy.len_factors() <= 20:
        area_strategy.run_in_linspace_compare_mode()
    else:
        area_strategy.run_in_linspace_count_mode(False)
