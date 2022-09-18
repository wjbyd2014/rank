import matplotlib
import matplotlib.pyplot as plt
import numpy as np


def draw_list_earn_money(ma3, ticks, title):
    len_ma3 = len(ma3)
    data3 = dict()
    data12 = dict()
    data30 = dict()
    data60 = dict()
    dataavg = dict()
    sum_price = 0

    for idx in range(len_ma3):
        data3[idx] = ma3[idx]
        sum_price += ma3[idx]
        dataavg[idx] = sum_price / (idx + 1)

        if idx > 2:
            data12[idx] = sum(ma3[idx - 3:idx + 1]) / 4
        if idx > 8:
            data30[idx] = sum(ma3[idx - 9:idx + 1]) / 10
        if idx > 18:
            data60[idx] = sum(ma3[idx - 19:idx + 1]) / 20

    print(data3)
    print(dataavg)

    xmin = 0
    xmax = len(ma3) - 1

    ymin = min([min(arr) for arr in [data3.values(), data12.values(), data30.values(), data60.values()]])
    ymax = max([max(arr) for arr in [data3.values(), data12.values(), data30.values(), data60.values()]])

    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(14, 7))

    idx = 0
    # legends = ['ma3', 'ma6', 'ma9', 'ma15', 'ma30', 'ma60', 'avg']
    # for data in [data3, data6, data9, data15, data30, data60, dataavg]:
    legends = ['ma3', 'ma12', 'ma30', 'ma60', 'avg']
    for data in [data3, data12, data30, data60, dataavg]:
        ax.plot(list(data.keys()), data.values(), label=legends[idx])
        idx += 1

    ax.set_xlim(xmin, xmax)  # x轴范围
    ax.set_ylim(ymin, ymax)  # y轴范围
    ax.set_yticks([*np.linspace(ymin, ymax, 20)])

    plt.xticks(list(data3.keys()), ticks, fontsize=8, rotation=90)
    ax.xaxis.set_major_locator(plt.MultipleLocator(20))
    plt.yticks(fontsize=8)
    plt.subplots_adjust(top=0.96, bottom=0.09, right=0.97, left=0.03, hspace=0.02, wspace=0.02)
    plt.title(title)
    plt.grid()
    plt.legend(fontsize=8)
    plt.show()


def load_ticks(code):
    ret = list()
    with open("D:\\share\\" + code + ".ticks") as file:
        for line in file:
            ret.append(line[:-1])
    return ret


def load_ma3(code):
    ret = list()
    with open("D:\\share\\" + code + ".ma3") as file:
        for line in file:
            price = int(line[:-1])
            ret.append(price)
    return ret


def count_zf(data):
    data.reverse()
    ret = []
    sum_d = 0
    for idx, d in enumerate(data):
        sum_d += d
        ret.append(sum_d / (idx + 1))
    return ret

if __name__ == '__main__':
    """data1 = list(range(20))
    data1 = data1 + [18, 16]
    data2 = [x for x in range(22) if x % 2 == 0]
    data3 = [-x * 2 for x in range(1,10)]
    data3.reverse()
    data4 = data3 + data2 + [18, 16]"""

    # code = "301269.SZA"
    # code = "688262.SHA"
    code = "688521.SHA" # 均线在成交价下面太久，导致成交机会比较少
    # code = "300339.SZA"
    # code = "603444.SHA"
    data_ma3 = load_ma3(code)
    ticks = load_ticks(code)
    assert len(data_ma3) == len(ticks)
    draw_list_earn_money(data_ma3, ticks, code + '均线图')
