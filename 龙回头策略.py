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
            data['可买金额'] = data['原始金额']
            data['原始金额'] = round(data['原始金额'] / 10000, 2)
            if data['is_st'] == 1:
                if data['可买金额'] > 200 * 10000:
                    data['可买金额'] = 200 * 10000
            else:
                data['可买金额'] *= 0.5
                if data['可买金额'] > 2000 * 10000:
                    data['可买金额'] = 2000 * 10000

    def select_stocks(self, data_list):
        super().select_stocks(data_list)

        for data in data_list:
            if data['本轮ma3第几次触发'] > self.cm.get_config_value('最大本轮触发次数'):
                data['淘汰原因'] = '触发次数'

    def sort_data_list_by_time(self, data_list):
        data_list.sort(key=lambda x: x['买入时间'])


if __name__ == '__main__':
    longhuitou_strategy = StrategyLongHuiTou('龙回头策略',
                                             'D:\\ts\\',
                                             ['当日排名', '淘汰原因', '是否买入'],
                                             '龙回头策略股票池.csv',
                                             {'日期': str, '代码': str, '名称': str,
                                              'is_st': int, '上市天数': float,
                                              '买入时间': str, '买入价': float, '原始金额': float,
                                              '涨停拉升': float, '涨停拉升时间': float,
                                              '200日涨停数': int,
                                              'ma3上涨起始日': str,
                                              'ma3涨停数量': int,
                                              'ma3最高价涨停数量': int,
                                              '本轮ma3第几次触发': int,
                                              '4日内最低价跌停次数': int,
                                              '本日涨停价和10日内最高最高价涨幅': float,
                                              '10日内最高最高价日期': str,
                                              '7日内上次涨停日期': str,
                                              '上次涨停距今几日': int,
                                              '上次涨停距今最高价最高涨幅': float,
                                              '上次涨停距今累计涨幅': float,
                                              '上次涨停距今阳线个数': int,
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
                                              '原始金额', '可买金额', '盈亏比', '计划买入金额', '计划买入盈亏金额', '实际买入金额', '实际盈亏金额',
                                              '当日排名', '买入时间', '是否买入'],
                                             ['买入量', '买入金额', '淘汰原因'], 20221208, 600)

    longhuitou_strategy.set_data_filter(lambda data: data['代码'][2:4] in ['60', '00'])
    longhuitou_strategy.set_sort_data_list(longhuitou_strategy.sort_data_list_by_time)
    longhuitou_strategy.init()
    longhuitou_strategy.load_data()
    """factors = ConfigManager.linspace2(yinxiang_strategy.get_data(), '开盘涨幅', 10)
    yinxiang_strategy.add_factor2('开盘价涨幅范围', factors)"""
    longhuitou_strategy.add_factor2('每日资金总量', [6000])
    longhuitou_strategy.add_factor2('单只股票购买上限', [2000])
    longhuitou_strategy.add_factor2('买入比', [100])
    longhuitou_strategy.add_factor2('尾部资金', [1])
    longhuitou_strategy.add_factor2('最大本轮触发次数', [5])
    longhuitou_strategy.gen_factors()

    len_factors = longhuitou_strategy.len_factors()
    print(f'len_factors = {len_factors}')

    if longhuitou_strategy.len_factors() == 1:
        longhuitou_strategy.run_in_normal_mode()
    elif longhuitou_strategy.len_factors() <= 20:
        longhuitou_strategy.run_in_linspace_compare_mode()
    else:
        longhuitou_strategy.run_in_linspace_count_mode(False)
