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
                data['淘汰原因'] = '买入量'
                continue

            if not self.data_filter(data):
                data['打分'] = 0
                continue

            if data['代码'][2:4] in ['60', '00']:
                tag = '10cm'
            else:
                tag = '20cm'

            if data['量比'] < self.cm.get_config_value(tag + '最小量比'):
                data['打分'] = 0
                data['淘汰原因'] = '最小量比'
                continue

            if data['开板次数'] > self.cm.get_config_value(tag + '最大开板次数'):
                data['打分'] = 0
                data['淘汰原因'] = '最大开板次数'
                continue

            if data['开板最大回撤'] > self.cm.get_config_value(tag + '最大开板最大回撤'):
                data['打分'] = 0
                data['淘汰原因'] = '最大开板最大回撤'
                continue

            if data['上市天数'] < self.cm.get_config_value(tag + '最小上市天数'):
                data['打分'] = 0
                data['淘汰原因'] = '最小上市天数'
                continue

            if data['涨板打断次数'] > self.cm.get_config_value(tag + '最大断板次数'):
                data['打分'] = 0
                data['淘汰原因'] = '最大断板次数'
                continue

            if data['可买金额'] < self.cm.get_config_value(tag + '最小可买金额') * 10000:
                data['打分'] = 0
                data['淘汰原因'] = '最小可买金额'
                continue

            if data['开盘最大回撤'] < self.cm.get_config_value(tag + '开盘最大回撤'):
                data['打分'] = 0
                data['淘汰原因'] = '开盘最大回撤'
                continue

            if data['开盘价涨幅'] < self.cm.get_config_value(tag + '开盘价最小涨幅'):
                data['打分'] = 0
                data['淘汰原因'] = '开盘价最小涨幅'
                continue

            if data['10日阴线数'] > self.cm.get_config_value(tag + '最大10日阴线数'):
                data['打分'] = 0
                data['淘汰原因'] = '最大10日阴线数'
                continue

            if data['3日十字阴线极值'] > self.cm.get_config_value(tag + '最大3日十字阴线极值'):
                data['打分'] = 0
                data['淘汰原因'] = '最大3日十字阴线极值'
                continue

            data['打分'] = data['平均面积']

            if data['1日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value(tag + '涨停板数1打分')
            if data['3日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value(tag + '涨停板数3打分') * (data['3日涨停板数'] - data['1日涨停板数'])
            if data['5日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value(tag + '涨停板数5打分') * (data['5日涨停板数'] - data['3日涨停板数'])
            if data['7日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value(tag + '涨停板数7打分') * (data['7日涨停板数'] - data['5日涨停板数'])
            if data['10日涨停板数'] > 0:
                data['打分'] += self.cm.get_config_value(tag + '涨停板数10打分') * (data['10日涨停板数'] - data['7日涨停板数'])

            data['打分'] += data['1日低位涨停板数'] * self.cm.get_config_value(tag + '1日低位涨停板数打分')
            data['打分'] += data['3日低位涨停板数'] * self.cm.get_config_value(tag + '3日低位涨停板数打分')
            data['打分'] += data['5日低位涨停板数'] * self.cm.get_config_value(tag + '5日低位涨停板数打分')
            data['打分'] += data['7日低位涨停板数'] * self.cm.get_config_value(tag + '7日低位涨停板数打分')
            data['打分'] += data['10日低位涨停板数'] * self.cm.get_config_value(tag + '10日低位涨停板数打分')

            data['打分'] += self.cm.get_config_value(tag + '最低点系数') * data['最低点']
            data['打分'] += self.cm.get_config_value(tag + '最高点系数') * data['最高点']

            if data['ma3向上'] == 1:
                data['打分'] += self.cm.get_config_value(tag + 'ma3向上系数')

            if data['ma5向上'] == 1:
                data['打分'] += self.cm.get_config_value(tag + 'ma5向上系数')

            if data['昨日是否一字板'] == 1:
                data['打分'] += self.cm.get_config_value(tag + '昨日一字板系数')

    def count_stock_area_earn_money(self, data_list, normal_mode):
        total_earn_money = 0
        total_use_money = 0

        data_list_20cm = [data for data in data_list if data['代码'][2:4] not in ['60', '00']]
        data_list_20cm.sort(key=lambda x: x['打分'], reverse=True)
        for idx, data in enumerate(data_list_20cm):
            data['当日排名'] = idx + 1

        total_money_20cm = self.max_use_money_per_day * self.cm.get_config_value('20cm资金比') * 10000
        earn_money_20cm, use_money_20cm, left_money_20cm = \
            self._count_stock_earn_money(
                data_list_20cm, total_money_20cm, self.cm.get_config_value('20cm尾部资金') * 10000, normal_mode)
        total_earn_money += earn_money_20cm
        total_use_money += use_money_20cm

        data_list_10cm = [data for data in data_list if data['代码'][2:4] in ['60', '00']]
        data_list_10cm.sort(key=lambda x: x['打分'], reverse=True)
        for idx, data in enumerate(data_list_10cm):
            data['当日排名'] = idx + 1

        total_money_10cm = self.max_use_money_per_day * (1 - self.cm.get_config_value('20cm资金比')) * 10000
        """if total_money_20cm > use_money_20cm:
            total_money_10cm += (total_money_20cm - use_money_20cm)"""
        earn_money_10cm, use_money_10cm, left_money10cm = \
            self._count_stock_earn_money(
                data_list_10cm, total_money_10cm, self.cm.get_config_value('10cm尾部资金') * 10000, normal_mode)
        total_earn_money += earn_money_10cm
        total_use_money += use_money_10cm

        if normal_mode:
            data_list.sort(key=lambda x: x['当日排名'], reverse=False)
        return total_earn_money, total_use_money, left_money10cm + left_money_20cm


if __name__ == '__main__':
    area_strategy = AreaStrategy('area_strategy_30cm',
                                 'D:\\ts\\',
                                 'area_strategy_30cm.csv',
                                 ['打分', '当日排名', '淘汰原因'],
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
                                  '7日低位涨停板数': int, '10日低位涨停板数': int,
                                  '10日阴线数': int, '3日十字阴线极值': float, '5日十字阴线极值': float, '10日十字阴线极值': float
                                  },
                                 'mianji_stock_info_day.js',
                                 {},
                                 ['日期', '代码', '名称', '可买金额', '盈亏金额', '盈亏比', '计划买入金额', '实际买入金额', '实际盈亏金额',
                                  '买入价', '卖出价', '卖出日期', '打分', '当日排名'],
                                 ['买入量'], 20220727, 300)

    area_strategy.add_factor2('10cm涨停板数1打分', [0.4])
    area_strategy.add_factor2('10cm涨停板数3打分', [0.9])
    area_strategy.add_factor2('10cm涨停板数5打分', [3.0])
    area_strategy.add_factor2('10cm涨停板数7打分', [0.3])
    area_strategy.add_factor2('10cm涨停板数10打分', [11.8])
    area_strategy.add_factor2('10cm最小上市天数', [200])
    area_strategy.add_factor2('10cm最小量比', [0.35])
    area_strategy.add_factor2('10cm尾部资金', [450])
    area_strategy.add_factor2('10cm买入比', [100])
    area_strategy.add_factor2('10cm最大开板次数', [5])
    area_strategy.add_factor2('10cm最大开板最大回撤', [6.3])
    area_strategy.add_factor2('10cm最高点系数', [0.5])
    area_strategy.add_factor2('10cm最低点系数', [0.2])
    area_strategy.add_factor2('10cm最大断板次数', [7])
    area_strategy.add_factor2('10cmma3向上系数', [-0.6])
    area_strategy.add_factor2('10cmma5向上系数', [-6.4])
    area_strategy.add_factor2('10cm昨日一字板系数', [-3.5])
    area_strategy.add_factor2('10cm最小可买金额', [300])
    area_strategy.add_factor2('10cm1日低位涨停板数打分', [0.6])
    area_strategy.add_factor2('10cm3日低位涨停板数打分', [0])
    area_strategy.add_factor2('10cm5日低位涨停板数打分', [0])
    area_strategy.add_factor2('10cm7日低位涨停板数打分', [2.9])
    area_strategy.add_factor2('10cm10日低位涨停板数打分', [0])
    area_strategy.add_factor2('10cm开盘最大回撤', [-6.8])
    area_strategy.add_factor2('10cm开盘价最小涨幅', [-6.3])
    area_strategy.add_factor2('10cm最大10日阴线数', [6])
    area_strategy.add_factor2('10cm最大3日十字阴线极值', [8])

    area_strategy.add_factor2('20cm涨停板数1打分', [10.4])
    area_strategy.add_factor2('20cm涨停板数3打分', [3.6])
    area_strategy.add_factor2('20cm涨停板数5打分', [0.1])
    area_strategy.add_factor2('20cm涨停板数7打分', [3.6])
    area_strategy.add_factor2('20cm涨停板数10打分', [7.7])
    area_strategy.add_factor2('20cm最小上市天数', [450])
    area_strategy.add_factor2('20cm最小量比', [0.3])
    area_strategy.add_factor2('20cm尾部资金', [300])  # 当买完一个股票后，资金不足300W时，就不继续买了，衡量资金利用率
    area_strategy.add_factor2('20cm买入比', [100])
    area_strategy.add_factor2('20cm最大开板次数', [3])
    area_strategy.add_factor2('20cm最大开板最大回撤', [10.8])
    area_strategy.add_factor2('20cm最高点系数', [0])
    area_strategy.add_factor2('20cm最低点系数', [0])
    area_strategy.add_factor2('20cm最大断板次数', [2])
    area_strategy.add_factor2('20cmma3向上系数', [-4.8])
    area_strategy.add_factor2('20cmma5向上系数', [-0.3])
    area_strategy.add_factor2('20cm昨日一字板系数', [-7.6])
    area_strategy.add_factor2('20cm最小可买金额', [200])  # 可买金额低于500W的直接跳过，衡量股票自身
    area_strategy.add_factor2('20cm1日低位涨停板数打分', [0])
    area_strategy.add_factor2('20cm3日低位涨停板数打分', [8.4])
    area_strategy.add_factor2('20cm5日低位涨停板数打分', [3.1])
    area_strategy.add_factor2('20cm7日低位涨停板数打分', [3.4])
    area_strategy.add_factor2('20cm10日低位涨停板数打分', [0.9])
    area_strategy.add_factor2('20cm开盘最大回撤', [-10.0])
    area_strategy.add_factor2('20cm开盘价最小涨幅', [-3.6])
    area_strategy.add_factor2('20cm最大10日阴线数', [7])
    area_strategy.add_factor2('20cm最大3日十字阴线极值', [11.5])

    area_strategy.add_factor2('20cm资金比', [0.5])

    len_factors = area_strategy.len_factors()
    print(f'len_factors = {len_factors}')

    area_strategy.init()

    if area_strategy.len_factors() == 1:
        area_strategy.run_in_normal_mode()
    elif area_strategy.len_factors() <= 20:
        area_strategy.run_in_linspace_compare_mode()
    else:
        area_strategy.run_in_linspace_count_mode(False)
