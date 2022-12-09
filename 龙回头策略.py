import utils
from strategy import *


class StrategyLongHuiTou(Strategy):
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
            data['可买金额'] = data['买入金额']

    def select_stocks(self, data_list):
        super().select_stocks(data_list)


if __name__ == '__main__':
    longhuitou_strategy = StrategyLongHuiTou('龙回头策略',
                                             'D:\\ts\\',
                                             ['当日排名', '淘汰原因', '是否买入'],
                                             '龙回头策略股票池.csv',
                                             {'日期': str, '代码': str, '名称': str,
                                              'is_st': int, '上市天数': float,
                                              '买入时间': str, '买入价': float, '买入金额': float,
                                              '10日涨停数': int, '20日涨停数': int,
                                              '30日涨停数': int, '40日涨停数': int,
                                              '10日最大大涨幅度': float, '10日最大大涨日期': str,
                                              '20日最大大涨幅度': float, '20日最大大涨日期': str,
                                              '30日最大大涨幅度': float, '30日最大大涨日期': str,
                                              '40日最大大涨幅度': float, '40日最大大涨日期': str
                                              },
                                             'longhuitou.js',
                                             {}, '', {}, '', {},
                                             ['日期', '代码', '名称',
                                              '可买金额', '盈亏比', '计划买入金额', '计划买入盈亏金额', '实际买入金额', '实际盈亏金额',
                                              '当日排名', '淘汰原因', '是否买入'],
                                             ['买入量'], 20221208, 300)

    longhuitou_strategy.init()
    longhuitou_strategy.load_data()
    """factors = ConfigManager.linspace2(yinxiang_strategy.get_data(), '开盘涨幅', 10)
    yinxiang_strategy.add_factor2('开盘价涨幅范围', factors)"""
    longhuitou_strategy.add_factor2('每日资金总量', [100000000])
    longhuitou_strategy.add_factor2('单只股票购买上限', [1600])
    longhuitou_strategy.add_factor2('买入比', [100])
    longhuitou_strategy.add_factor2('尾部资金', [1])
    longhuitou_strategy.gen_factors()

    len_factors = longhuitou_strategy.len_factors()
    print(f'len_factors = {len_factors}')

    if longhuitou_strategy.len_factors() == 1:
        longhuitou_strategy.run_in_normal_mode()
    elif longhuitou_strategy.len_factors() <= 20:
        longhuitou_strategy.run_in_linspace_compare_mode()
    else:
        longhuitou_strategy.run_in_linspace_count_mode(False)
