import sys
import json
import re

sys.path.append("D:\Tinysoft\Analyse.NET")
import TSLPy3 as tspy


class TinySoft:
    def __init__(self, work_dir):
        self.work_dir = work_dir

    @staticmethod
    def tsbytestostr(data):
        if isinstance(data, tuple) or isinstance(data, list):
            lent = len(data)
            ret = []

            for i in range(lent):
                ret.append(TinySoft.tsbytestostr(data[i]))
        elif isinstance(data, dict):
            ret = {}
            for i in data:
                ret[TinySoft.tsbytestostr(i)] = TinySoft.tsbytestostr(data[i])
        elif isinstance(data, bytes):
            ret = data.decode('gbk', errors='ignore')
        else:
            ret = data
        return ret

    @staticmethod
    def F执行函数(func_name, pmlist):
        if not tspy.Logined():
            TinySoft.F连接服务器()
        data1 = tspy.RemoteCallFunc(func_name,
                                    pmlist, {})
        data1 = TinySoft.tsbytestostr(data1[1])
        return data1

    @staticmethod
    def F执行语句(ts_str, pmdict=None, unencode=True):
        if not tspy.Logined():
            TinySoft.F连接服务器()

        if pmdict is not None:
            ts_str1 = ts_str.format(**pmdict)
            datar = tspy.RemoteExecute(ts_str1, {})
        else:
            datar = tspy.RemoteExecute(ts_str, {})
        data1 = datar[1]
        if not unencode:
            return data1
        if type(data1) == bytes:
            data1 = json.loads(data1)
        if type(data1) != list:
            print('F执行语句不是list', TinySoft.tsbytestostr(datar), ts_str)
            return []
        return data1

    @staticmethod
    def F生成天软日期_str(one_day: str):
        one_day = re.split('[-/]', one_day)
        ts_day = tspy.EncodeDate(int(one_day[0]), int(one_day[1]), int(one_day[2]))
        return ts_day

    def F读取脚本文件(self, filename):
        with open(self.work_dir + filename, 'r', encoding='utf-8') as f:
            ts_str = f.read()
        return ts_str

    @staticmethod
    def F连接服务器(b配置文件=True):
        if not tspy.Logined():
            if b配置文件:
                dl = tspy.DefaultConnectAndLogin("test")
            else:
                tspy.ConnectServer("219.143.214.209", 888)
                # ts.ConnectServer("211.100.23.205",443)
                dl = tspy.LoginServer("liuzhiyong", "Zoos_600809")  # Tuple(ErrNo,ErrMsg) 登陆用户
            if dl[0] == 0:
                print("登陆成功")
                print("服务器设置:", tspy.GetService())
                tspy.SetComputeBitsOption(64)  # 设置计算单位
                print("计算位数设置:", tspy.GetComputeBitsOption())
                data = tspy.RemoteExecute("return 'return a string';", {})  # 执行一条语句
                print("数据:", data)
            else:
                print("登陆失败", TinySoft.tsbytestostr(dl[1]))
            return
        print('已连接,无需重连')

    @staticmethod
    def F断开服务器():
        if tspy.Logined():
            tspy.Disconnect()  # 断开连接
            print('断开成功')
        print('未连接,无需断开')

    def get_dates(self, day, num):
        code = self.F读取脚本文件("dates.js")
        return self.F执行语句(code, {'day': day, 'num': num})

    def __del__(self):
        TinySoft.F断开服务器()


"""if __name__ == '__main__':
    ts = TinySoft("D:\\ts\\")
    ts.F断开服务器()
    ts.F连接服务器(b配置文件=False)

    ret_dates = ts.get_dates(20220718)
    print(ret_dates)

    date = ts.F生成天软日期_str('2022-07-18')
    print(date)"""
