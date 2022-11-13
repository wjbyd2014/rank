import utils
from strategy import *


def sort_data_list(data_list):
    data_list.sort(key=lambda x: x['score'], reverse=True)


class StrategyYinXiang(Strategy):
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
            data['可买金额'] = 1000 * 10000
            data['买入价'] = data['开盘价']
            if data['历史最高换手率'] == 0:
                data['换手率比'] = 0
            else:
                data['换手率比'] = round(data['昨日换手率'] / data['历史最高换手率'], 2)

        factor1 = utils.guiyihua(data_list, '印象')
        factor2 = utils.guiyihua(data_list, '相对大盘涨幅')
        factor3 = utils.guiyihua(data_list, '换手率比')
        factor4 = utils.guiyihua(data_list, '阳线实体')

        for i in range(len(data_list)):
            data_list[i]['印象打分'] = factor1[i]
            data_list[i]['相对大盘涨幅打分'] = factor2[i]
            data_list[i]['换手率比打分'] = factor3[i]
            data_list[i]['阳线实体打分'] = factor4[i]
            data_list[i]['score'] = factor1[i] + factor2[i] + factor3[i] + factor4[i]

    def select_stocks(self, data_list):
        super().select_stocks(data_list)

        for data in data_list:
            if data['换手率比'] < 0.8:
                data['淘汰原因'] = '换手率比'
                break
            elif data['昨日成交金额'] < 400000000:
                data['淘汰原因'] = '昨日成交金额'
                break
            elif data['过去2到10天最大成交金额'] < 400000000:
                data['淘汰原因'] = '过去2到10天最大成交金额'
                break
            elif data['10日涨停数'] <= 0:
                data['淘汰原因'] = '10日涨停数'
                break


if __name__ == '__main__':
    yinxiang_strategy = StrategyYinXiang('印象分策略',
                                         'D:\\ts\\',
                                         ['当日排名', '淘汰原因',
                                          'score', '印象打分',
                                          '阳线实体打分',
                                          '相对大盘涨幅打分',
                                          '换手率比打分',
                                          '换手率比', '买入价', '是否买入'],
                                         '印象分策略股票池.csv',
                                         {'日期': str, '代码': str, '名称': str,
                                          '昨日涨幅': float, '相对大盘涨幅': float, '昨日成交金额': float, '过去2到10天最大成交金额': float,
                                          '7日涨停数': int, '10日涨停数': int, '15日涨停数': int,
                                          '创10日新高': int, '创15日新高': int,
                                          'ma5上涨起始日': str, 'ma10上涨起始日': str,
                                          '开盘涨幅': float, '开盘价': float, '买入量': float,
                                          '昨日换手率': float, '历史最高换手率': float, '历史最高换手率日': str,
                                          '印象': float, '阳线实体': float,
                                          '上市天数': float
                                          },
                                         'yinxiang.js',
                                         {}, '', {}, '', {},
                                         ['日期', '代码', '名称'],
                                         ['买入量', '开盘价'], 20221108, 400)

    yinxiang_strategy.set_sort_data_list(sort_data_list)

    yinxiang_strategy.init()
    yinxiang_strategy.load_data()
    """factors = ConfigManager.linspace2(zhuiban_strategy.get_data(), '开盘价涨幅', 10)
    zhuiban_strategy.add_factor2('开盘价涨幅范围', factors)"""
    yinxiang_strategy.add_factor2('每日资金总量', [6000])
    yinxiang_strategy.add_factor2('单只股票购买上限', [1600])
    yinxiang_strategy.add_factor2('买入比', [100])
    yinxiang_strategy.add_factor2('尾部资金', [1])
    yinxiang_strategy.gen_factors()

    len_factors = yinxiang_strategy.len_factors()
    print(f'len_factors = {len_factors}')

    if yinxiang_strategy.len_factors() == 1:
        yinxiang_strategy.run_in_normal_mode()
    elif yinxiang_strategy.len_factors() <= 20:
        yinxiang_strategy.run_in_linspace_compare_mode()
    else:
        yinxiang_strategy.run_in_linspace_count_mode(False)
