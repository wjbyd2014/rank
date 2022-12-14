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
        self.reload = False

    def build_cache(self):
        if not os.path.exists(self.csv_file_name):
            return

        with open(self.csv_file_name, mode='r', newline='') as csv_file:
            self.reload = True
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
            if self.reload:
                return list()
            print(f'{self.name} downloading {date}')
            js_params = {'day': date}
            for param_name, param_value in self.other_params.items():
                js_params[param_name] = param_value

            ts_data = self.ts.F执行语句(self.code, js_params)

            for data in ts_data:
                if not self.fd:
                    new_file = not os.path.exists(self.csv_file_name)
                    self.fd = open(self.csv_file_name, mode='a', newline='')
                    self.writer = csv.DictWriter(self.fd, fieldnames=['key', '日期'] + list(data.keys()))
                    if new_file:
                        self.writer.writeheader()

                data['key'] = date_str + '|' + data['代码']
                data['日期'] = date_str
                self.writer.writerow(data)
            self.cache[date] = ts_data
            return ts_data

    def __del__(self):
        if self.fd:
            self.fd.close()


class ReadWriteDateKeyCsvCache:
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
                if row['key'] in self.cache:
                    print('重复key({}) in {}'.format(row['key'], self.name))
                    return False

                data = {'key': row['key']}
                for field_name, filed_converter in self.fields_dict.items():
                    data[field_name] = filed_converter(row[field_name])
                self.cache[row['key']] = data

    def keys(self):
        return list(self.fields_dict.keys())

    def get(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            key_ = key.split('|')
            if len(key_) != 2:
                return None

            day = key_[0]
            one_day = day.split('-')
            day = int(one_day[0]) * 10000 + int(one_day[1]) * 100 + int(one_day[2])

            print(f'{self.name} downloading {day}')
            js_params = {'day': day}
            for param_name, param_value in self.other_params.items():
                js_params[param_name] = param_value

            ts_data = self.ts.F执行语句(self.code, js_params)
            for data in ts_data:
                if not self.fd:
                    new_file = not os.path.exists(self.csv_file_name)
                    self.fd = open(self.csv_file_name, mode='a', newline='')
                    self.writer = csv.DictWriter(self.fd, fieldnames=['key'] + list(data.keys()))
                    if new_file:
                        self.writer.writeheader()

                data['key'] = key_[0] + '|' + data['代码']
                data_to_ret = {}
                for field in ['key'] + self.keys():
                    data_to_ret[field] = data[field]
                self.writer.writerow(data)
                self.cache[data['key']] = data_to_ret
            return self.cache[key]

    def __del__(self):
        if self.fd:
            self.fd.close()


"""if __name__ == '__main__':
    test_work_dir = 'D:\\ts\\'
    test_ts = TinySoft(test_work_dir)
    test_ts.F断开服务器()
    test_ts.F连接服务器(b配置文件=False)
    stock_info_cache = ReadWriteDateKeyCsvCache('stock_info_cache', test_work_dir,
                                                {'名称': str, '代码': str, '上市天数': float, 'ma3向上': int, 'ma5向上': int,
                                                 '上涨起点日': str, '涨板打断次数': int,
                                                 '开盘价涨幅': float, '昨日是否一字板': int
                                                 }, test_ts, 'stock_info_day.js',
                                                {}, 'test_mianji_stock_info_day.csv')
    stock_info_cache.build_cache()
    ret_date = test_ts.get_dates(20220727, 2)
    ret_date.reverse()

    test_date_key = dict()
    test_ts_dates = [date['date'] for date in ret_date]
    for date in ret_date:
        date_str = date['datestr']
        test_key = date_str+'|SH600000'
        test_value = stock_info_cache.get(test_key)
        print(f'{test_key} = ', test_value)"""
