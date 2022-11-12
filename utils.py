def guiyihua(list_data, key):
    if not list_data:
        return []

    ret = list()
    min_ = min([data[key] for data in list_data])
    max_ = max([data[key] for data in list_data])

    if min_ == max_:
        return [0] * len(list_data)

    for data in list_data:
        ret.append((data[key] - min_) / (max_ - min_))

    return ret


if __name__ == '__main__':
    print(guiyihua([1, 5, 3, 8, 2, 4, 0, 100]))
