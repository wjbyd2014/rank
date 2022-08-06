from strategy import *


class AreaStrategy(Strategy):
    def __init__(self, name, work_dir, csv_file_name, csv_field_names,
                 stock_pool_file_name, stock_pool_fields, stock_pool_js_file_name, stock_pool_js_params,
                 stock_info_file_name, stock_info_fields, stock_info_js_file_name, stock_info_js_params,
                 priority_fields, skipped_csv_fields, begin_date, date_num):
        super().__init__(name, work_dir, csv_file_name, csv_field_names,
                         stock_pool_file_name, stock_pool_fields, stock_pool_js_file_name, stock_pool_js_params,
                         stock_info_file_name, stock_info_fields, stock_info_js_file_name, stock_info_js_params,
                         priority_fields, skipped_csv_fields, begin_date, date_num)

    def __del__(self):
        super().__del__()

    def select_stocks(self, data_list):
        for data in data_list:
            if data['买入量'] == 0:
                data['打分'] = 0
                continue

            if not self.data_filter(data):
                data['打分'] = 0
                continue

            if data['量比'] < self.cm.get_config_value('最小量比'):
                data['打分'] = 0
                continue

            if data['开板次数'] > self.cm.get_config_value('最大开板次数'):
                data['打分'] = 0
                continue

            if data['开板最大回撤'] > self.cm.get_config_value('最大开板最大回撤'):
                data['打分'] = 0
                continue

            if data['上市天数'] < self.cm.get_config_value('最小上市天数'):
                data['打分'] = 0
                continue

            if data['涨板打断次数'] > self.cm.get_config_value('最大断板次数'):
                data['打分'] = 0
                continue

            if data['可买金额'] < self.cm.get_config_value('最小可买金额') * 10000:
                data['打分'] = 0
                continue

            if data['开盘最大回撤'] < self.cm.get_config_value('开盘最大回撤'):
                data['打分'] = 0
                continue

            if data['开盘价涨幅'] < self.cm.get_config_value('开盘价最小涨幅'):
                data['打分'] = 0
                continue

            data['打分'] = data['平均面积']

            if data['1日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value('涨停板数1打分')
            if data['3日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value('涨停板数3打分') * (data['3日涨停板数'] - data['1日涨停板数'])
            if data['5日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value('涨停板数5打分') * (data['5日涨停板数'] - data['3日涨停板数'])
            if data['7日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value('涨停板数7打分') * (data['7日涨停板数'] - data['5日涨停板数'])
            if data['10日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value('涨停板数10打分') * (data['10日涨停板数'] - data['7日涨停板数'])

            data['打分'] += data['1日低位涨停板数'] * self.cm.get_config_value('1日低位涨停板数打分')
            data['打分'] += data['3日低位涨停板数'] * self.cm.get_config_value('3日低位涨停板数打分')
            data['打分'] += data['5日低位涨停板数'] * self.cm.get_config_value('5日低位涨停板数打分')
            data['打分'] += data['7日低位涨停板数'] * self.cm.get_config_value('7日低位涨停板数打分')
            data['打分'] += data['10日低位涨停板数'] * self.cm.get_config_value('10日低位涨停板数打分')

            data['打分'] += self.cm.get_config_value('最低点系数') * data['最低点']
            data['打分'] += self.cm.get_config_value('最高点系数') * data['最高点']

            if data['ma3向上'] == 1:
                data['打分'] *= self.cm.get_config_value('ma3向上系数')

            if data['ma5向上'] == 1:
                data['打分'] *= self.cm.get_config_value('ma5向上系数')

            if data['昨日是否一字板'] == 1:
                data['打分'] *= self.cm.get_config_value('昨日一字板系数')


if __name__ == '__main__':
    area_strategy = AreaStrategy('area_strategy_20cm',
                                 'D:\\ts\\',
                                 'area_strategy_20cm.csv',
                                 ['打分', '当日排名'],
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
                                  'time3': '09:54:00', 'time4': '09:58:00', 'num': 800},
                                 '新面积策略股票信息.csv',
                                 {'名称': str, '代码': str, '上市天数': float, 'ma3向上': int, 'ma5向上': int,
                                  '上涨起点日': str, '涨板打断次数': int,
                                  '开盘价涨幅': float, '昨日是否一字板': int,
                                  '1日低位涨停板数': int, '3日低位涨停板数': int, '5日低位涨停板数': int,
                                  '7日低位涨停板数': int, '10日低位涨停板数': int
                                  },
                                 'mianji_stock_info_day.js',
                                 {},
                                 ['日期', '代码', '名称', '可买金额', '盈亏金额', '盈亏比', '计划买入金额', '实际买入金额', '实际盈亏金额',
                                  '买入价', '卖出价', '卖出日期', '打分', '当日排名'],
                                 ['买入量'], 20220727, 300)

    area_strategy.add_factor2('涨停板数1打分', [10.4])
    area_strategy.add_factor2('涨停板数3打分', [3.6])
    area_strategy.add_factor2('涨停板数5打分', [0.01])
    area_strategy.add_factor2('涨停板数7打分', [3.6])
    area_strategy.add_factor2('涨停板数10打分', [7.7])
    area_strategy.add_factor2('最小上市天数', [800])
    area_strategy.add_factor2('最小量比', [0.7])
    area_strategy.add_factor2('尾部资金', [300])
    area_strategy.add_factor2('买入比', [100])
    area_strategy.add_factor2('最大开板次数', [3])
    area_strategy.add_factor2('最大开板最大回撤', [10.4])
    area_strategy.add_factor2('最高点系数', [0])
    area_strategy.add_factor2('最低点系数', [0])
    area_strategy.add_factor2('最大断板次数', [2])
    area_strategy.add_factor2('ma3向上系数', [0.88])
    area_strategy.add_factor2('ma5向上系数', [0.86])
    area_strategy.add_factor2('昨日一字板系数', [0.61])
    area_strategy.add_factor2('最小可买金额', [500])
    area_strategy.add_factor2('1日低位涨停板数打分', [0])
    area_strategy.add_factor2('3日低位涨停板数打分', [8])
    area_strategy.add_factor2('5日低位涨停板数打分', [0])
    area_strategy.add_factor2('7日低位涨停板数打分', [0])
    area_strategy.add_factor2('10日低位涨停板数打分', [0])
    area_strategy.add_factor2('开盘最大回撤', [-11.5])
    area_strategy.add_factor2('开盘价最小涨幅', [-4])

    area_strategy.set_max_use_money_per_day(3000)
    area_strategy.set_data_filter(lambda data: data['代码'][2:4] not in ['60', '00'])

    len_factors = area_strategy.len_factors()
    print(f'len_factors = {len_factors}')

    area_strategy.init()

    if area_strategy.len_factors() == 1:
        area_strategy.run_in_normal_mode()
    elif area_strategy.len_factors() <= 20:
        area_strategy.run_in_linspace_compare_mode()
    else:
        area_strategy.run_in_linspace_count_mode(False)
