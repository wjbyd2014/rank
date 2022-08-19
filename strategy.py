from abc import abstractmethod
from csv_cache import *
from tinysoft import *
from config_manager import *
from strategy_utils import *
import os


def sort_data_list(data_list):
    data_list.sort(key=lambda x: x['打分'], reverse=True)


class Strategy:
    def __init__(self, name, work_dir, csv_field_names,
                 stock_pool_file_name, stock_pool_fields, stock_pool_js_file_name, stock_pool_js_params,
                 stock_info_file_name, stock_info_fields, stock_info_js_file_name, stock_info_js_params,
                 priority_fields, skipped_csv_fields, begin_date, date_num):
        self.name = name
        self.ts = TinySoft(work_dir)
        self.sell_cache = ReadOnlyCsvCache('sell_cache', work_dir,
                                           {'卖出价': float, '卖出日期': str},
                                           ['卖出明细30.csv', '卖出明细30_未完全卖出.csv'])
        self.csv_field_names = ['key']

        self.stock_pool_cache = ReadWriteDateCsvCache('stock_pool_cache', work_dir,
                                                      stock_pool_fields,
                                                      self.ts,
                                                      stock_pool_js_file_name,
                                                      stock_pool_js_params,
                                                      stock_pool_file_name)
        self.csv_field_names += self.stock_pool_cache.keys()

        self.stock_info_cache = None
        if stock_info_file_name:
            self.stock_info_cache = ReadWriteDateKeyCsvCache('stock_info_cache', work_dir,
                                                             stock_info_fields,
                                                             self.ts,
                                                             stock_info_js_file_name,
                                                             stock_info_js_params,
                                                             stock_info_file_name)
            self.csv_field_names += self.stock_info_cache.keys()

        self.csv_field_names += csv_field_names + ['卖出价', '卖出日期', '可买金额',
                                                   '盈亏金额', '盈亏比', '计划买入金额', '实际买入金额',
                                                   '实际盈亏金额']

        list_fileds = self.csv_field_names.copy()
        self.csv_field_names = ['key'] + priority_fields
        for field in list_fileds:
            if field in self.csv_field_names or field in skipped_csv_fields:
                continue
            self.csv_field_names.append(field)

        self.skipped_csv_fields = skipped_csv_fields
        self.work_dir = work_dir
        self.csv_file_name = name + '.csv'
        self.bak_csv_file_name = name + '.bak.csv'
        self.ts_dates = None
        self.date_key = dict()
        self.cm = ConfigManager(work_dir + '回测.txt')
        self.list_factors = None
        self.date_to_stock_data = dict()
        self.fd = None
        self.writer = None
        self.data_filter = lambda data: True
        self.earn_money_list = list()
        self.begin_date = begin_date
        self.date_num = date_num
        self.sort_data_list = sort_data_list
        self.list_legends = []

    def __del__(self):
        if self.fd:
            self.fd.close()

    def init(self):
        self.ts.F断开服务器()
        self.ts.F连接服务器(b配置文件=False)
        self.sell_cache.build_cache()
        self.stock_pool_cache.build_cache()
        if self.stock_info_cache:
            self.stock_info_cache.build_cache()

    def set_data_filter(self, data_filter):
        self.data_filter = data_filter

    def set_sort_data_list(self, func):
        self.sort_data_list = func

    def run_in_normal_mode(self):
        self.__run(False, False, True, True)
        self.__draw_picture1()

    def run_in_linspace_compare_mode(self, list_legends=None):
        self.__run(False, False, True, False)
        self.__draw_picture2(self.list_legends)

    def run_in_linspace_count_mode(self, do_print=False):
        self.__run(True, do_print, False, False)

    def __run(self, do_print1, do_print2, do_collect_earn_money, normal_mode):
        max_earn_money_ratio = 0
        max_earn_money = 0
        best_factors = None
        len_list_factors = self.len_factors()
        num = 0
        for factors in self.list_factors:
            num += 1
            self.cm.update_configs(factors)

            if do_collect_earn_money and not normal_mode:
                legend_str = ''
                for i, config_name in enumerate(self.cm.config_values):
                    config_value = self.cm.get_config_value(config_name)
                    if len(self.cm.list_factors[i]) > 1:
                        legend_str += f'{config_name}:{config_value},'
                self.list_legends.append(legend_str[:-1])

            total_earn_money = 0
            total_use_money = 0
            earn_money = dict()
            for date in self.ts_dates:
                data_list_copy = self.date_to_stock_data[date].copy()
                self.pre_count_buy_amount(data_list_copy)
                self.__count_buy_amount(data_list_copy)
                self.post_count_buy_amount(data_list_copy)
                self.select_stocks(data_list_copy)
                got_money, use_money, left_money = \
                    self.count_stock_area_earn_money(data_list_copy, normal_mode)

                if left_money > 0:
                    print(f"{date} left {left_money}\n")

                if normal_mode:
                    self.__write_csv(data_list_copy)

                earn_money[date] = got_money
                total_earn_money += got_money
                total_use_money += use_money

            earn_money_ratio = total_earn_money * 10000 / total_use_money
            if earn_money_ratio > max_earn_money_ratio:
                max_earn_money = total_earn_money
                max_earn_money_ratio = earn_money_ratio
                best_factors = factors

                if not normal_mode:
                    self.cm.log(max_earn_money_ratio)

            if do_print1 and num % 100 == 0:
                print("num = ", num, ' 当前最大收益 = ', max_earn_money_ratio)

            if do_print2:
                self.cm.print(num, len_list_factors, total_earn_money, earn_money_ratio)

            if do_collect_earn_money:
                self.earn_money_list.append(earn_money)

        print('best_factors = ', best_factors)
        print('max_earn_money_ratio = ', round(max_earn_money_ratio))
        print('max_earn_money = ', max_earn_money)

    def gen_factors(self):
        if not self.cm.list_factors:
            return False

        self.__gen_factors()

    def load_data(self):
        self.__gen_dates()
        for date in self.ts_dates:
            stock_data = self.stock_pool_cache.get(date, self.date_key[date])
            if not stock_data:
                print("stock_pool_cache.get failed, date = ", date)
                return False

            data_list = list()
            for data in stock_data:
                if self.stock_info_cache:
                    stock_info = self.stock_info_cache.get(data['key'])
                    if not stock_info:
                        print("stock_info_cache.get failed, key = ", data['key'])
                        return False

                    for key in self.stock_info_cache.keys():
                        data[key] = stock_info[key]

                if not self.data_filter(data):
                    continue

                sell_info = self.sell_cache.get(data['key'])
                if not sell_info:
                    print("sell_cache.get failed, key = ", data['key'])
                    continue

                data['卖出价'] = sell_info['卖出价']
                data['卖出日期'] = sell_info['卖出日期']

                data_list.append(data)
            self.date_to_stock_data[date] = data_list
        return True

    def __gen_dates(self):
        ret_date = self.ts.get_dates(self.begin_date, self.date_num)
        ret_date.reverse()

        self.ts_dates = [date['date'] for date in ret_date]
        for date in ret_date:
            self.date_key[date['date']] = date['datestr']

    def len_factors(self):
        return self.cm.len_factors()

    def add_factor1(self, name, min_value, max_value, interval):
        self.cm.add_factor1(name, min_value, max_value, interval)

    def add_factor2(self, name, factors):
        self.cm.add_factor2(name, factors)

    def __gen_factors(self):
        self.list_factors = self.cm.gen_factors()

    def pre_count_buy_amount(self, data_list):
        for data in data_list:
            data['实际买入量'] = data['买入量']

    def post_count_buy_amount(self, data_list):
        pass

    def __count_buy_amount(self, data_list):
        use_money_per_stock = self.cm.get_config_value('单只股票购买上限') * 10000

        for data in data_list:
            data['可买金额'] = data['计划买入金额'] = data['盈亏金额'] = data['盈亏比'] = 0
            if data['买入价'] > 0 and data['实际买入量'] > 0:
                data['可买金额'] = round(data['买入价'] * data['实际买入量'])
                data['计划买入金额'] = data['可买金额']

                if data['计划买入金额'] > use_money_per_stock:
                    data['计划买入金额'] = use_money_per_stock

                data['盈亏比'] = round((data['卖出价'] / data['买入价'] - 1) * 100, 2)
                data['盈亏金额'] = round((data['卖出价'] - data['买入价']) * data['实际买入量'])

    def __write_csv(self, data_list):
        if not self.fd:
            if os.path.exists(self.work_dir + self.csv_file_name):
                if os.path.exists(self.work_dir + self.bak_csv_file_name):
                    os.remove(self.work_dir + self.bak_csv_file_name)
                os.rename(self.work_dir + self.csv_file_name, self.work_dir + self.bak_csv_file_name)
            self.fd = open(self.work_dir + self.csv_file_name, mode='w', newline='')
            self.writer = csv.DictWriter(self.fd, fieldnames=self.csv_field_names)
            self.writer.writeheader()

        for data in data_list:
            data_to_write = {}
            for field in self.csv_field_names:
                if field not in self.skipped_csv_fields:
                    data_to_write[field] = data.get(field, '')

            data_to_write['买入价'] = round(data_to_write['买入价'], 3)
            data_to_write['可买金额'] = round(data_to_write['可买金额'] / 10000, 2)
            data_to_write['盈亏金额'] = round(data_to_write['盈亏金额'] / 10000, 2)
            data_to_write['计划买入金额'] = round(data_to_write['计划买入金额'] / 10000, 2)
            data_to_write['实际买入金额'] = round(data_to_write['实际买入金额'] / 10000, 2)
            data_to_write['实际盈亏金额'] = round(data_to_write['实际盈亏金额'] / 10000, 2)
            self.writer.writerow(data_to_write)

    def __draw_picture1(self):
        draw_earn_money(self.earn_money_list[0], self.work_dir, self.name + '收益图', False)

    def __draw_picture2(self, list_legends):
        draw_list_earn_money(self.earn_money_list, list_legends, self.work_dir, self.name + '收益图', True)

    @abstractmethod
    def select_stocks(self, data_list):
        pass

    def count_stock_area_earn_money(self, data_list, normal_mode):
        self.sort_data_list(data_list)
        for idx, data in enumerate(data_list):
            data['当日排名'] = idx + 1
        return self._count_stock_earn_money(
            data_list, self.cm.get_config_value('每日资金总量') * 10000, self.cm.get_config_value('尾部资金') * 10000, normal_mode)

    def _count_stock_earn_money(self, data_list, total_money, retain_money, normal_mode):
        total_earn_money = 0
        total_use_money = 0
        left_money = total_money
        buy_vol_ratio = self.cm.get_config_value('买入比')

        for data in data_list:
            if left_money > 0 and not data.get('淘汰原因'):
                if data['计划买入金额'] > left_money:
                    data['实际买入金额'] = left_money
                else:
                    data['实际买入金额'] = data['计划买入金额']

                data['实际买入金额'] *= buy_vol_ratio / 100

                if data['代码'][0:2] == 'SH':
                    service_fee = 上交所手续费
                else:
                    service_fee = 深交所手续费
                real_buy_vol = int(data['实际买入金额'] / data['买入价'])
                data['实际买入金额'] = data['买入价'] * real_buy_vol
                real_use_money = data['实际买入金额'] * (1 + service_fee)
                total_use_money += real_use_money
                left_money -= real_use_money
                data['实际盈亏金额'] = real_buy_vol * data['卖出价'] * (1 - service_fee - 印花税) - real_use_money
                total_earn_money += data['实际盈亏金额']
                if left_money < retain_money:
                    left_money = 0
            else:
                data['实际买入金额'] = data['实际盈亏金额'] = 0
                if not normal_mode:
                    break
        return total_earn_money, total_use_money, left_money

    def get_data(self):
        return self.date_to_stock_data
