import os
import csv
from tinysoft import TinySoft


class ReadOnlyCsvCache:
    def __init__(self, name, work_dir, fields_dict, input_csv_file):
        self.cache = dict()
        self.name = name
        self.work_dir = work_dir
        self.fields_dict = fields_dict
        self.input_csv_file = list()
        for csv_file in input_csv_file:
            self.input_csv_file.append(work_dir + csv_file)

    def build_cache(self):
        for csv_file in self.input_csv_file:
            if not os.path.exists(csv_file):
                print(f"{self.name} 输入文件 {csv_file} 未找到")
                continue

            with open(csv_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    key = row['key']
                    data = {}
                    for field_name, filed_converter in self.fields_dict.items():
                        data[field_name] = filed_converter(row[field_name])

                    if key in self.cache and self.cache[key] != data:
                        print(f'重复key{key} in {self.name}, 而且value不一致')
                        continue

                    self.cache[key] = data
        return True

    def get(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            return None


class ReadWriteKeyCsvCache:
    def __init__(self, name, work_dir, fields_dict, ts, code_file_name, other_params, csv_file_name):
        self.cache = dict()
        self.name = name
        self.ts = ts
        self.code = ts.F读取脚本文件(code_file_name)
        self.other_params = other_params
        self.csv_file_name = work_dir + csv_file_name
        self.fields_dict = fields_dict
        self.fd = None
        self.writer = None

    def build_cache(self):
        if not os.path.exists(self.csv_file_name):
            return True

        with open(self.csv_file_name, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row['key'] in self.cache:
                    print('重复key({}) in {}'.format(row['key'], self.name))
                    return False

                data = {'key': row['key']}
                for field_name, filed_converter in self.fields_dict.items():
                    data[field_name] = filed_converter(row[field_name])
                self.cache[row['key']] = data
        return True

    def keys(self):
        return list(self.fields_dict.keys())

    def get(self, key):
        if key in self.cache:
            return self.cache[key]

        key_ = key.split('|')
        if len(key_) != 2:
            return None

        print(f'{self.name} downloading {key}')
        day = key_[0]
        stock = key_[1]
        js_params = {'day': self.ts.F生成天软日期_str(day), 'stock_code': stock[2:]}
        for param_name, param_value in self.other_params.items():
            js_params[param_name] = param_value
        ret_data = self.ts.F执行语句(self.code, js_params)

        if not self.fd:
            new_file = not os.path.exists(self.csv_file_name)
            self.fd = open(self.csv_file_name, mode='a', newline='')
            self.writer = csv.DictWriter(self.fd, fieldnames=['key'] + self.keys())
            if new_file:
                self.writer.writeheader()

        data = {'key': key}
        for field_name in self.fields_dict:
            data[field_name] = ret_data[0][field_name]
        self.cache[key] = data
        self.writer.writerow(data)
        return self.cache[key]

    def __del__(self):
        if self.fd:
            self.fd.close()


class ReadWriteDateCsvCache:
    def __init__(self, name, work_dir, fields_dict, ts, code_file_name, other_params, csv_file_name):
        self.cache = dict()
        self.name = name
        self.ts = ts
        self.code = ts.F读取脚本文件(code_file_name)
        self.other_params = other_params
        self.csv_file_name = work_dir + csv_file_name
        self.fields_dict = fields_dict
        self.fd = None
        self.writer = None

    def build_cache(self):
        if not os.path.exists(self.csv_file_name):
            return

        with open(self.csv_file_name, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                key = row['key']
                key_ = key.split('|')
                if len(key_) != 2:
                    return None

                day = key_[0]
                one_day = day.split('-')
                day = int(one_day[0]) * 10000 + int(one_day[1]) * 100 + int(one_day[2])
                data = {'key': key}
                for field_name, filed_converter in self.fields_dict.items():
                    data[field_name] = filed_converter(row[field_name])
                self.cache.setdefault(day, list())
                self.cache[day].append(data)

    def keys(self):
        return list(self.fields_dict.keys())

    def get(self, date, date_str):
        if date in self.cache:
            return self.cache[date]
        else:
            print(f'{self.name} downloading {date}')
            js_params = {'day': date}
            for param_name, param_value in self.other_params.items():
                js_params[param_name] = param_value

            ts_data = self.ts.F执行语句(self.code, js_params)

            if not self.fd:
                new_file = not os.path.exists(self.csv_file_name)
                self.fd = open(self.csv_file_name, mode='a', newline='')
                self.writer = csv.DictWriter(self.fd, fieldnames=['key'] + self.keys())
                if new_file:
                    self.writer.writeheader()

            for data in ts_data:
                data['key'] = date_str + '|' + data['代码']
                data['日期'] = date_str
                self.writer.writerow(data)
            self.cache[date] = ts_data
            return ts_data

    def __del__(self):
        if self.fd:
            self.fd.close()

'''
if __name__ == '__main__':
    work_dir = 'D:\\ts\\'
    sell_cache = ReadOnlyCsvCache('sell_cache', work_dir,
                                  {'卖出价': float, '卖出日期': str},
                                  ['卖出明细30.csv', '卖出明细30_未完全卖出.csv', '1.txt'])
    sell_cache.build_cache()
    v1 = sell_cache.get('2022-07-08|SH605319')
    print(v1)
    v2 = sell_cache.get('2021-04-20|SH688600')
    print(v2)

    ts = TinySoft(work_dir)
    ts.F断开服务器()
    ts.F连接服务器(b配置文件=False)
    pkje_cache = ReadWriteKeyCsvCache('pkje_cache', work_dir,
                                      {'竞价涨幅': float, '买一价': float, '盘口金额': float, '早盘跌停盘口比': float},
                                      ts, 'pankoujine.js', {}, 'pkje.csv')
    pkje_cache.build_cache()
    v1 = pkje_cache.get('2022-06-02|SH688150')
    print(v1)
    v2 = pkje_cache.get('2022-06-02|SZ000957')
    print(v2)
    v3 = pkje_cache.get('2022-07-22|SZ000957')
    print(v3)

    area_cache = ReadWriteDateCsvCache('area_cache', work_dir,
                                       {'日期': str, '代码': str, '名称': str, '量比': float, '上市天数': int, '买入量': float,
                                        '1日涨停板数': int, '3日涨停板数': int, '5日涨停板数': int, '7日涨停板数': int,
                                        '是否涨停': int, '观察期收盘价涨幅': float, 'ma30向上': int,
                                        '交叉点': str, '面积': float,
                                        '观察期结束可以直接买入': int, '观察期结束直接买入价': float,
                                        '大回撤开始时间': str, '大回撤结束时间': str, '大回撤买入价': float,
                                        '上一波谷形成时间': str, '双波谷触发时间': str, '双波谷买入价': float, '双波谷涨幅': float,
                                        '双波谷前开板次数': int, '双波谷前最大开板回撤': float},
                                       ts,
                                       'mianji.js', {'time1': '09:33:00', 'time2': '09:52:00', 'num': 800},
                                       'mianji.csv'
                                       )
    area_cache.build_cache()
    v1 = area_cache.get(20220718, '2022-07-18')
    print(len(v1))
    v2 = area_cache.get(20220715, '2022-07-15')
    print(len(v2))
'''
