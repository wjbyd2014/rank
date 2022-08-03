from abc import abstractmethod
from csv_cache import *
from tinysoft import *
from config_manager import *
from strategy_utils import *


class Strategy:
    def __init__(self, name, work_dir, csv_file_name, csv_field_names,
                 stock_pool_file_name, stock_pool_fields, stock_pool_js_file_name, stock_pool_js_params,
                 stock_info_file_name, stock_info_fields, stock_info_js_file_name, stock_info_js_params,
                 priority_fields, skipped_csv_fields):
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

        if stock_info_file_name:
            self.stock_info_cache = ReadWriteKeyCsvCache('stock_info_cache', work_dir,
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
        self.csv_file_name = csv_file_name
        self.ts_dates = None
        self.date_key = dict()
        self.cm = ConfigManager(work_dir + '回测.txt')
        self.list_factors = None
        self.date_to_stock_data = dict()
        self.fd = None
        self.writer = None
        self.earn_money_list = list()
        self.max_use_money_per_day = 3000
        self.max_use_money_per_stock = 1800
        self.buy_vol_ratio = 100

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

    def run_in_normal_mode(self):
        if not self.__prepare():
            return

        self.__run(False, False, True, True, True)
        self.__draw_picture1()

    def run_in_linspace_compare_mode(self):
        list_legends = []
        for factors in self.cm.list_factors:
            if len(factors) > 1:
                list_legends = factors

        assert list_legends
        if not self.__prepare():
            return

        self.__run(False, False, True, False, False)
        self.__draw_picture2(list_legends)

    def run_in_linspace_count_mode(self, do_print=False):
        if not self.__prepare():
            return

        self.__run(do_print, True, False, False, False)

    def __run(self, do_print1, do_print2, do_collect_earn_money, count_all, write_csv):
        max_earn_money_ratio = 0
        max_earn_money = 0
        best_factors = None
        len_list_factors = self.len_factors()
        num = 0
        for factors in self.list_factors:
            num += 1
            self.cm.update_configs(factors)

            total_earn_money = 0
            total_use_money = 0
            earn_money = dict()
            for date in self.ts_dates:
                data_list_copy = self.date_to_stock_data[date].copy()
                self.select_stocks(data_list_copy)
                got_money, use_money, left_money = \
                    self.count_stock_area_earn_money(data_list_copy, count_all)

                if left_money > 0:
                    print(f"{date} left {left_money}\n")

                if write_csv:
                    self.__write_csv(data_list_copy)

                earn_money[date] = got_money
                total_earn_money += got_money
                total_use_money += use_money

            earn_money_ratio = total_earn_money * 10000 / total_use_money
            if earn_money_ratio > max_earn_money_ratio:
                max_earn_money = total_earn_money
                max_earn_money_ratio = earn_money_ratio
                best_factors = factors
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

    def __prepare(self):
        if not self.cm.list_factors:
            return False

        self.__gen_dates()
        self.__gen_factors()

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

                sell_info = self.sell_cache.get(data['key'])
                if not sell_info:
                    print("sell_cache.get failed, key = ", data['key'])
                    continue

                data['卖出价'] = sell_info['卖出价']
                data['卖出日期'] = sell_info['卖出日期']

                data_list.append(data)
            self.__count_buy_amount(data_list)
            self.date_to_stock_data[date] = data_list
        return True

    def __gen_dates(self):
        ret_date = self.ts.get_dates(20220727)
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

    def __count_buy_amount(self, data_list):
        use_money_per_stock = self.max_use_money_per_stock * 10000
        for data in data_list:
            data['可买金额'] = data['计划买入金额'] = data['盈亏金额'] = data['盈亏比'] = 0

            if data['买入价'] > 0 and data['买入量'] > 0:
                data['可买金额'] = round(data['买入价'] * data['买入量'])
                data['计划买入金额'] = data['可买金额'] * self.buy_vol_ratio / 100

                if data['计划买入金额'] > use_money_per_stock:
                    data['计划买入金额'] = use_money_per_stock

                data['盈亏比'] = round((data['卖出价'] / data['买入价'] - 1) * 100, 2)
                data['盈亏金额'] = round((data['卖出价'] - data['买入价']) * data['买入量'])

    def __write_csv(self, data_list_copy):
        if not self.fd:
            self.fd = open(self.work_dir + self.csv_file_name, mode='w', newline='')
            self.writer = csv.DictWriter(self.fd, fieldnames=self.csv_field_names)
            self.writer.writeheader()

        for data in data_list_copy:
            for key in self.skipped_csv_fields:
                data.pop(key)

            data['买入价'] = round(data['买入价'], 3)
            data['可买金额'] = round(data['可买金额'] / 10000, 2)
            data['盈亏金额'] = round(data['盈亏金额'] / 10000, 2)
            data['计划买入金额'] = round(data['计划买入金额'] / 10000, 2)
            data['实际买入金额'] = round(data['实际买入金额'] / 10000, 2)
            data['实际盈亏金额'] = round(data['实际盈亏金额'] / 10000, 2)
            self.writer.writerow(data)

    def __draw_picture1(self):
        draw_earn_money(self.earn_money_list[0], self.work_dir, self.name + '收益图', False)

    def __draw_picture2(self, list_legends):
        draw_list_earn_money(self.earn_money_list, list_legends, self.work_dir, self.name + '收益图', True)

    @abstractmethod
    def select_stocks(self, data_list_copy):
        pass

    def count_stock_area_earn_money(self, data_list_copy, count_all):
        ret = 0
        use_money = 0
        left_money = self.max_use_money_per_day * 10000
        min_use_money_per_stock = self.cm.get_config_value('每只股票最小购买金额') * 10000

        for data in data_list_copy:
            if left_money > 0 and data['打分'] > 0:
                if data['计划买入金额'] > left_money:
                    data['实际买入金额'] = left_money
                else:
                    data['实际买入金额'] = data['计划买入金额']

                if data['代码'][0:2] == 'SH':
                    service_fee = 上交所手续费
                else:
                    service_fee = 深交所手续费
                real_buy_vol = int(data['实际买入金额'] / data['买入价'])
                data['实际买入金额'] = data['买入价'] * real_buy_vol
                real_use_money = data['实际买入金额'] * (1 + service_fee)
                use_money += real_use_money
                left_money -= real_use_money
                data['实际盈亏金额'] = real_buy_vol * data['卖出价'] * (1 - service_fee - 印花税) - real_use_money
                ret += data['实际盈亏金额']
                if left_money < min_use_money_per_stock:
                    left_money = 0
            else:
                data['实际买入金额'] = data['实际盈亏金额'] = 0
                if not count_all:
                    break
        return ret, use_money, left_money
