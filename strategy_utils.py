import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

上交所手续费 = 0.00013
深交所手续费 = 0.00011
印花税 = 0.001


def draw_earn_money(day_earn_money, work_dir, title, show_picture):
    earn_money = 0
    d = dict()
    for day in day_earn_money:
        earn_money += day_earn_money[day]
        d[pd.to_datetime(str(day))] = [earn_money / 10000]

    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['axes.unicode_minus'] = False

    df = pd.DataFrame(d.values(), index=list(d.keys()), columns=['总收益'])
    ymax = df.max().max()
    ymin = df.min().min()
    xmax = df.index.max()
    xmin = df.index.min()

    ax1 = df.plot(figsize=(14, 6), yticks=[*np.linspace(ymin, ymax, 20)], rot=90, sharey=False,
                  subplots=False, grid=True, fontsize=8)

    alldays = matplotlib.dates.DayLocator(interval=5)  # 主刻度为每月
    ax1.xaxis.set_major_locator(alldays)  # 设置主刻度
    ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y%m%d'))  # 主刻度格式为年月日
    ax1.xaxis.set_minor_formatter(plt.NullFormatter())  # 取消副刻度
    ax1.set_xlim(xmin, xmax)  # x轴范围
    ax1.set_ylim(ymin, ymax)  # y轴范围
    plt.subplots_adjust(top=0.96, bottom=0.09, right=0.97, left=0.03, hspace=0.02, wspace=0.02)
    plt.title(title)
    if show_picture:
        plt.show()
    else:
        f = plt.gcf()  # 获取当前图像
        path = work_dir + '{}.png'.format(title)
        f.savefig(path)