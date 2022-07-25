import os
import csv


class ReadOnlyCsvCache(object):
    def __init__(self, name, fields_dict, input_csv_file):
        self.cache = dict()
        self.name = name
        self.fields_dict = fields_dict
        self.input_csv_file = input_csv_file

    def build_cache(self):
        for csv_file in self.input_csv_file:
            if not os.path.exists(csv_file):
                print(f"{self.name}输入文件{csv_file}未找到")
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


if __name__ == '__main__':
    work_dir = 'D:\\ts\\'
    sell_cache = ReadOnlyCsvCache('sell_cache',
                                  {'卖出价': float, '卖出日期': str},
                                  [work_dir + '卖出明细30.csv', work_dir + '卖出明细30_未完全卖出.csv', '1.txt'])
    sell_cache.build_cache()
    v1 = sell_cache.get('2022-07-08|SH605319')
    print(v1)
    v2 = sell_cache.get('2021-04-20|SH688600')
    print(v2)
