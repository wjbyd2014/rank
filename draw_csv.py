import matplotlib
import matplotlib.pyplot as plt
import numpy as np


def draw_list_earn_money(ma3, ticks, title):
    len_ma3 = len(ma3)
    data3 = dict()
    data6 = dict()
    data9 = dict()
    data15 = dict()
    data30 = dict()
    data60 = dict()
    dataavg = dict()
    sum_price = 0

    above = 0
    for idx in range(len_ma3):
        data3[idx] = ma3[idx]
        sum_price += ma3[idx]
        dataavg[idx] = sum_price / (idx + 1)

        if data3[idx] > dataavg[idx]:
            above += 1

        if idx > 0 and (idx + 1) % 2 == 0:
            data6[idx] = sum(ma3[idx - 1:idx + 1]) / 2
        if idx > 0 and (idx + 1) % 3 == 0:
            data9[idx] = sum(ma3[idx - 2:idx + 1]) / 3
        if idx > 0 and (idx + 1) % 5 == 0:
            data15[idx] = sum(ma3[idx - 4:idx + 1]) / 5
        if idx > 0 and (idx + 1) % 10 == 0:
            data30[idx] = sum(ma3[idx - 9:idx + 1]) / 10
        if idx > 0 and (idx + 1) % 20 == 0:
            data60[idx] = sum(ma3[idx - 19:idx + 1]) / 20

    print(f"len = {len(data_ma3)}, above = {above}")

    xmin = 0
    xmax = len(ma3) - 1

    ymin = min([min(arr) for arr in [data3.values(), data6.values(), data9.values(),
                                     data15.values(), data30.values(), data60.values()]])
    ymax = max([max(arr) for arr in [data3.values(), data6.values(), data9.values(),
                                     data15.values(), data30.values(), data60.values()]])

    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(14, 7))

    idx = 0
    # legends = ['ma3', 'ma6', 'ma9', 'ma15', 'ma30', 'ma60']
    # for data in [data3, data6, data9, data15, data30, data60]:
    legends = ['ma3', 'ma15', 'ma30', 'ma60', 'avg']
    for data in [data3, data15, data30, data60, dataavg]:
        ax.plot(list(data.keys()), data.values(), label=legends[idx])
        idx += 1

    ax.set_xlim(xmin, xmax)  # x轴范围
    ax.set_ylim(ymin, ymax)  # y轴范围
    ax.set_yticks([*np.linspace(ymin, ymax, 20)])

    plt.xticks(list(data3.keys()), ticks, fontsize=8, rotation=90)
    ax.xaxis.set_major_locator(plt.MultipleLocator(10))
    plt.yticks(fontsize=8)
    plt.subplots_adjust(top=0.96, bottom=0.09, right=0.97, left=0.03, hspace=0.02, wspace=0.02)
    plt.title(title)
    plt.grid()
    plt.legend(fontsize=8)
    plt.show()


def load_ticks(code):
    ret = list()
    with open("D:\\download\\" + code + ".ticks") as file:
        for line in file:
            ret.append(line[:-1])
    return ret


def load_ma3(code):
    ret = list()
    with open("D:\\download\\" + code + ".ma3") as file:
        for line in file:
            price = int(line[:-1])
            ret.append(price)
    return ret


if __name__ == '__main__':
    code = "003000.SZA"  # 一字板
    code = "600400.SHA"  # 涨停板
    code = "603530.SHA"  # 跌停板
    data_ma3 = load_ma3(code)
    ticks = load_ticks(code)
    assert len(data_ma3) == len(ticks)
    draw_list_earn_money(data_ma3, ticks, code + '均线图')
