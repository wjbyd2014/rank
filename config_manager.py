class ConfigManager:
    def __init__(self, log_path):
        self.list_factors = list()
        self.config_values = dict()
        self.log_fd = open(log_path, 'w')

    def add_factor1(self, name, min_value, max_value, interval):
        self.list_factors.append(self.分箱(min_value, max_value, interval))
        self.config_values[name] = None

    def add_factor2(self, name, factors):
        self.list_factors.append(factors)
        self.config_values[name] = None

    @staticmethod
    def 分箱(min_value, max_value, interval):
        ret = list()
        value = min_value
        while value <= max_value:
            ret.append(value)
            value += interval
            value = round(value, 2)
        return ret

    def get_config_value(self, config_name):
        return self.config_values[config_name]

    def update_configs(self, list_config_values):
        assert (len(list_config_values) == len(self.config_values))
        i = 0
        for config_name in self.config_values:
            self.config_values[config_name] = list_config_values[i]
            i += 1

    def gen_factors(self):
        return self.__gen_factors(self.list_factors)

    def __gen_factors(self, list_params):
        if len(list_params) == 1:
            for param in list_params[0]:
                yield [param]
        else:
            list_factor = self.__gen_factors(list_params[1:])
            for factor in list_factor:
                for param in list_params[0]:
                    yield [param] + factor

    def len_factors(self):
        ret = 1
        for factors in self.list_factors:
            ret *= len(factors)
        return ret

    def log(self, max_total_earn_money):
        log_str = ''
        if self.log_fd:
            for config_name in self.config_values:
                log_str += config_name + '=' + str(self.config_values[config_name]) + ' '
            log_str += '收益 = {}\n'.format(max_total_earn_money)
            self.log_fd.write(log_str)
            self.log_fd.flush()

    def print(self, num, len_list_factors, total_earn_money, earn_money_ratio):
        log_str = f'{num}/{len_list_factors} '
        for config_name in self.config_values:
            log_str += config_name + '=' + str(self.config_values[config_name]) + ' '
        log_str += f'实际收益 = {total_earn_money} 收益率 = {earn_money_ratio}'
        print(log_str)

    def __del__(self):
        if self.log_fd:
            self.log_fd.close()


'''
if __name__ == '__main__':
    cm = ConfigManager('cm.txt')
    cm.add_factor1('v1', 1, 2, 1)
    cm.add_factor1('v2', 3, 4, 1)
    cm.add_factor1('v3', 5, 6, 1)
    cm.add_factor2('v4', ['a','b'])
    print(cm.len_factors())

    list_factors = cm.gen_factors()
    i = 0
    for factors in list_factors:
        i += 1
        cm.update_configs(factors)
        cm.log(1.2345)
        print(cm.get_config_value('v1'), ' ', cm.get_config_value('v2'), ' ', cm.get_config_value('v3'), ' ', cm.get_config_value('v4'))
'''
