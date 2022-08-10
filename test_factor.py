import csv_cache
from strategy import *


class AreaStrategy(Strategy):
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

    def pre_process_data(self, data_list):
        point = 0.5
        for data in data_list:
            data['卖出价'] *= (1 - point / 100)

    def select_stocks(self, data_list):
        for data in data_list:
            data['打分'] = 0

            if data['10日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value('涨停板数10打分') * (data['10日涨停板数'] - data['5日涨停板数'])
                data['打分'] += self.cm.get_config_value('可买金额放大系数') * data['buy_amount_weight']

    def post_process_data(self, data_list):
        list_buy_amount = [data['可买金额'] for data in data_list]
        buy_amount_weight = fit_transform(list_buy_amount)
        assert len(buy_amount_weight) == len(data_list)
        i = 0
        for data in data_list:
            data['buy_amount_weight'] = round(buy_amount_weight[i], 3)
            i += 1


if __name__ == '__main__':
    area_strategy = AreaStrategy('test_factor',
                                 'D:\\ts\\',
                                 ['打分', '当日排名', 'buy_amount_weight', '淘汰原因'],
                                 '新面积策略股票池.csv',
                                 {'日期': str, '代码': str, '名称': str, '量比': float,
                                  '买入量': float, '买入价': float,
                                  '交叉点': str, '总面积': float, '平均面积': float,
                                  '开板次数': int, '开板最大回撤': float, '最高点': float, '最低点': float,
                                  '1日涨停板数': int, '3日涨停板数': int, '5日涨停板数': int, '7日涨停板数': int, '10日涨停板数': int,
                                  '开盘最大回撤': float
                                  },
                                 'mianji_stock_poll.js',
                                 {'time1': '09:33:00', 'time2': '09:53:00',
                                  'time3': '09:54:00', 'time4': '09:58:00', 'num': 800, 'min_avg_area': -2},
                                 None, None, None, None, [], [],
                                 20220727, 300)

    area_strategy.add_factor2('涨停板数10打分', [10])
    area_strategy.add_factor2('尾部资金', [10])
    area_strategy.add_factor2('可买金额放大系数', [25])

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
