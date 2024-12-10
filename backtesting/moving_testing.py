'''
思路：
快慢均线上下穿透，并设置观察期，初版不加杠杆，只做多
'''
import pathlib
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger
root_dir = pathlib.Path(__file__).resolve().parent.parent

'''
===========================实盘慎用.在观摩了git回测代码后手敲的回测实现方案=======================================
'''


class moving:

    def __init__(self):
        self.FastPeriod = 5  # 入市快线周期
        self.SlowPeriod = 20  # 入市慢线周期
        # self.EnterPeriod = 2  # 入市观察期
        self.ExitFastPeriod = 5  # 离市快线周期
        self.ExitSlowPeriod = 20  # 离市慢线周期
        # self.ExitPeriod = True  # 离市观察期
        self.PositionRatio = 0.8  # 仓位比例
        self.StopLossRatio = 0.05  # 止损比率
        self.Interval = 10  # 轮询周期(秒)
        self.instId = ''
        self.bar = ''
        self.bar_df = ''
        self.money = 0  # 总金额
        self.current_value = 0  # 当前币种金额
        self.STATE_IDLE = -1  # -1空仓。long，short
        self.cost = 0

    def strategy(self, ts):
        logger.info(ts, self.current_value)
        # 空仓
        state = self.STATE_IDLE
        entryPrice = 0  # 成本
        self.bar_df = pd.read_csv('{}/history_data/history_data_{}_{}.csv'.format(root_dir, self.instId, self.bar))
        self.bar_df['ts'] = self.bar_df['ts'].astype(str)
        self.current_value = self.bar_df.loc[self.bar_df['ts'] == ts, 'c'].tolist()[0]

        datetime_time = datetime.strptime(ts, "%Y-%m-%d")
        pre_obj = datetime_time - timedelta(days=2)
        pre = pre_obj.strftime("%Y-%m-%d")
        pre_fastPeriod = self.bar_df.loc[self.bar_df['ts'] == pre, 'ma{}'.format(self.FastPeriod)].tolist()[0]
        pre_slowPeriod = self.bar_df.loc[self.bar_df['ts'] == pre, 'ma{}'.format(self.SlowPeriod)].tolist()[0]

        now_obj = datetime_time - timedelta(days=1)
        now = now_obj.strftime("%Y-%m-%d")
        fastPeriod = self.bar_df.loc[self.bar_df['ts'] == now, 'ma{}'.format(self.FastPeriod)].tolist()[0]
        slowPeriod = self.bar_df.loc[self.bar_df['ts'] == now, 'ma{}'.format(self.SlowPeriod)].tolist()[0]

        file_name = 'testing_{}_{}.csv'.format(self.instId, self.bar)
        file_path = '{}/history_data/{}'.format(root_dir, file_name)

        testing_df = pd.read_csv(file_path)


        if (pre_fastPeriod < pre_slowPeriod) and (fastPeriod > slowPeriod):
            if testing_df.shape[0] == 0:
                # 开多单
                logger.info('无记录下初始单--------------------')
                num = round(self.money / self.current_value - 0.01, 2)
                remaining = round(self.money - self.current_value * num, 2)
                all = round(remaining + self.current_value * num, 2)
                data = [[ts, 'b', self.current_value, num, remaining, all]]
                df = pd.DataFrame(data, columns=['ts', 'operate', 'value', 'num', 'remaining', 'all'])
                df.to_csv(file_path, index=False)
                self.order(data)
                self.cost = self.current_value
                operrate_date = [ts, 'b', self.current_value, num, remaining, all]
                self.order(operrate_date)
                self.STATE_IDLE = 'long'
            else:
                # 无持仓下单
                logger.info('无持仓则下单--------------------')
                num = round(testing_df.iloc[-1]['all'] / self.current_value - 0.01, 2)
                remaining = round(testing_df.iloc[-1]['all'] - self.current_value * num, 2)
                all = round(remaining + self.current_value * num, 2)
                data = [ts, 'b', self.current_value, num, remaining, all]
                testing_df.loc[len(testing_df.index)] = data
                testing_df.to_csv(file_path, index=False)
                self.order(data)
                self.cost = self.current_value
        elif (pre_fastPeriod > pre_slowPeriod) and (fastPeriod < slowPeriod):
            if testing_df.shape[0] == 0:
                logger.info('初始无操作')
                data = [[ts, 'o', self.current_value, 0, self.money, self.money]]
                df = pd.DataFrame(data, columns=['ts', 'operate', 'value', 'num', 'remaining', 'all'])
                df.to_csv(file_path, index=False)
            else:
                if self.cost == 0:
                    # 已经无持仓
                    logger.info('已无持仓')
                    data = [ts, 'o', self.current_value, 0, testing_df.iloc[-1]['remaining'],
                            testing_df.iloc[-1]['all']]
                    testing_df.loc[len(testing_df.index)] = data
                    testing_df.to_csv(file_path, index=False)
                else:
                    # 卖出
                    logger.info('卖出')
                    remaining = round(
                        testing_df.iloc[-1]['remaining'] + testing_df.iloc[-1]['num'] * self.current_value, 2)
                    data = [ts, 's', self.current_value, 0, remaining, remaining]
                    testing_df.loc[len(testing_df.index)] = data
                    testing_df.to_csv(file_path, index=False)
                    self.cost = 0
                    self.order(data)
        else:
            if testing_df.shape[0] == 0:
                logger.info('初始无操作')
                data = [[ts, 'o', self.current_value, 0, self.money, self.money]]
                df = pd.DataFrame(data, columns=['ts', 'operate', 'value', 'num', 'remaining', 'all'])
                df.to_csv(file_path, index=False)
            else:
                # 不动
                logger.info('不动')
                remaining = testing_df.iloc[-1]['remaining']
                all = round(remaining + self.current_value * testing_df.iloc[-1]['num'], 2)
                data = [ts, 'o', self.current_value, testing_df.iloc[-1]['num'], remaining, all]
                testing_df.loc[len(testing_df.index)] = data
                testing_df.to_csv(file_path, index=False)



    def order(self, *args):
        # todo这里可以继续添加发送邮箱等操作
        logger.info(args)





