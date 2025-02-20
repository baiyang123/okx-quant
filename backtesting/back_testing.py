from datetime import datetime, timedelta

import pandas as pd
from matplotlib import pyplot as plt

from backtesting.grid_testing import Grid_Testing
from config import ORDER_COLUMNS
from factory.MarketFactory import MarketFactory
from backtesting.moving_testing import moving


import sys
import os

import pathlib

root_dir = pathlib.Path(__file__).resolve().parent.parent

'''
回测总触发器
'''


class back_testing:

    def __init__(self):
        pass

    def backtesting(self, instId, before, after, bar, money, lever, class_name):
        # 1. 获取区间数据, 并生成
        class_name.money = money
        class_name.instId = instId
        class_name.bar = bar

        # 由于时差okx时间线需要向后平移两天
        datetime_time = datetime.strptime(after, "%Y-%m-%d")
        after_obj = datetime_time - timedelta(days=-2)
        after = after_obj.strftime("%Y-%m-%d")

        res, msg, income, percentage = MarketFactory().get_history_data(instId, before, after, bar)
        # 准备持仓文件
        file_name = 'testing_{}_{}_{}.csv'.format(class_name.__class__.__name__, instId, bar)
        file_path = '{}/history_data/{}'.format(root_dir, file_name)
        if class_name.__class__.__name__ == 'moving':
            columns = ['ts', 'operate', 'value', 'num', 'remaining', 'all']
        elif class_name.__class__.__name__ == 'Grid_Testing':
            columns = ORDER_COLUMNS
        if not os.path.exists(file_path):
            with open(file_path, "w") as file:
                pass
        else:
            df = pd.DataFrame(columns=columns)
            df.to_csv(file_path, index=False)

        if res:
            df = pd.read_csv('{}/history_data/history_data_{}_{}.csv'.format(root_dir, instId, bar))
            df_sorted_by_column = df.sort_values(by='ts', ascending=True)
            # 由于均线理论从前两天的均线看所以向后平移两天
            i = 2
            while i < df_sorted_by_column.shape[0]:
                if class_name.__class__.__name__ == 'Grid_Testing':
                    i = i+20 # 要算boll等数据20天后才有
                df_ts = df_sorted_by_column.iloc[i]
                i = i + 1
                # todo getattr 写法
                class_name.current_value = df_ts.loc['c']
                # for循环将每天的实时价格传给类的策略,其余由策略决定是否买卖，买卖后回来计算
                class_name.strategy(df_ts.loc['ts'])
                print(i)
            # 计算收益
            # file_name = 'testing_{}_{}.csv'.format(instId, bar)
            # file_path = '{}/history_data/{}'.format(root_dir, file_name)

            df_testing = pd.read_csv(file_path)

            fig, ax = plt.subplots()

            value_start = df_testing.loc[0]['value']
            all_start = df_testing.loc[0]['all']

            plt.plot(pd.to_datetime(df_testing['ts']), round(df_testing['all']/all_start, 2), label='all')
            if class_name.__class__.__name__ == 'moving':
                plt.plot(pd.to_datetime(df_testing['ts']), round(df_testing['value']/value_start, 2), label='value')
            elif class_name.__class__.__name__ == 'Grid_Testing':
                plt.plot(pd.to_datetime(df_testing['ts']), round(df_testing['value'] / value_start, 2), label='current_value')

            plt.xlabel('时间')
            plt.ylabel('总收益')
            # x轴倾斜45读
            plt.xticks(rotation=45)
            # 控制画板自适应大小
            fig.tight_layout()
            # 显示图例
            plt.legend()
            # 设置Matplotlib的中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.show()


if __name__ == '__main__':
    instId, before, after, bar, money, lever, class_name = 'BTC-USDT-SWAP', '2023-03-05', '2024-11-05', '1D', 50000, 3, moving()
    back_testing().backtesting(instId, before, after, bar, money, lever, class_name)
    # instId, before, after, bar, money, lever, class_name = 'BTC-USDT-SWAP', '2023-03-05', '2024-11-01', '1D', 100000, 3,Grid_Testing()
    # back_testing().backtesting(instId, before, after, bar, money, lever, class_name)
