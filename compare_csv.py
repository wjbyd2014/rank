import csv
import os

fileds = ['key', '日期', '代码', '名称', '可买金额', '盈亏金额', '盈亏比', '计划买入金额', '实际买入金额', '实际盈亏金额', '打分', '当日排名']


def parse_csv(file_name):
    if not os.path.exists(file_name):
        return

    ret = dict()
    with open(file_name, mode='r', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row['实际买入金额'] == '0':
                continue

            data = {}
            for field in fileds:
                data[field] = row[field]
            ret[data['key']] = data
    return ret


if __name__ == '__main__':
    work_dir = 'D://ts//'
    new_file = work_dir + 'area_strategy_10cm.csv'
    bak_file = work_dir + 'area_strategy_10cm.bak.csv'
    result_file = work_dir + 'diff.csv'

    ret_new = parse_csv(new_file)
    ret_bak = parse_csv(bak_file)

    list_add = []
    list_del = []
    list_diff = []
    for key in ret_new:
        if key not in ret_bak:
            list_add.append(key)
        elif key in ret_bak:
            data_new = ret_new[key]
            data_bak = ret_bak[key]
            if ret_new[key] != ret_bak[key]:
                list_diff.append(key)

    for key in ret_bak:
        if key not in ret_new:
            list_del.append(key)

    if not list_add and not list_del and not list_diff:
        exit(0)

    fd = open(result_file, mode='w', newline='')
    writer = csv.DictWriter(fd, fieldnames=fileds+['action'])
    writer.writeheader()
    for new_key in list_add:
        data_new = ret_new[new_key]
        data_new['action'] = '新增'
        writer.writerow(data_new)

    for del_key in list_del:
        data_del = ret_bak[del_key]
        data_del['action'] = '删除'
        writer.writerow(data_del)

    for diff_key in list_diff:
        data_new = ret_new[diff_key]
        data_del = ret_bak[diff_key]
        data = {'action': '修改'}
        for field in fileds:
            data[field] = data_new[field]

        data['计划买入金额'] = float(data_new['计划买入金额']) - float(data_del['计划买入金额'])
        if data['计划买入金额'] >= 0:
            data['计划买入金额'] = '增加' + str(data['计划买入金额'])
        else:
            data['计划买入金额'] = '减少' + str(data['计划买入金额'])

        data['实际买入金额'] = float(data_new['实际买入金额']) - float(data_del['实际买入金额'])
        if data['实际买入金额'] >= 0:
            data['实际买入金额'] = '增加' + str(data['实际买入金额'])
        else:
            data['实际买入金额'] = '减少' + str(data['实际买入金额'])

        data['实际盈亏金额'] = float(data_new['实际盈亏金额']) - float(data_del['实际盈亏金额'])
        if data['实际盈亏金额'] > 0:
            data['实际盈亏金额'] = '增加' + str(data['实际盈亏金额'])
        else:
            data['实际盈亏金额'] = '减少' + str(data['实际盈亏金额'])
        writer.writerow(data)
    fd.close()
