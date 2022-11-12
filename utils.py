def guiyihua(list_data):
    ret = list()
    min_ = min(list_data)
    max_ = max(list_data)

    for data in list_data:
        ret.append((data - min_) / (max_ - min_))

    return ret


if __name__ == '__main__':
    print(guiyihua([1, 5, 3, 8, 2, 4, 0, 100]))
