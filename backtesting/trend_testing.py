'''
思路：
1. 获取最近30天的最高最低价，取最高最最低价，且最后一天的最高最低价不能是最高最低价
2. 监测价格，突破后开仓3 5 10
3. 设置止损为无利润点，如果到了10倍之后，且20日线大于无利润止损点，则每日将止损点太高至20线
4. 要有买卖日志，发消息
'''
import pathlib
from datetime import datetime, timedelta

import pandas as pd
from pandas import DataFrame

from factory.MarketFactory import MarketFactory
from okx import Trade, MarketData, Account
from schemas.base_model import BaseOrder

root_dir = pathlib.Path(__file__).resolve().parent.parent

# 趋势玩法，5日线上穿20先则买入，下传则卖出
class trend:

    def __init__(self):
        # 初始化趋势策略下单相关属性
        # self.base_inst = BaseOrder(base_dict)
        # 初始化账号
        api_key = 'd759cf97-a1b3-40da-9c49-911629d7b3b6'
        api_secret_key = 'C8C89E3E0D6FA34530F1BBD2C33DFDBF'
        passphrase = ''
        # self.tradeApi = Trade.TradeAPI(api_key, api_secret_key, passphrase, False, '0')
        # self.marketApi = MarketData.MarketAPI(api_key, api_secret_key, passphrase, False, '0')
        # self.accountAPI = Account.AccountAPI(api_key, api_secret_key, passphrase, False, '0')
        self.current_ts = ''
        self.current_value = 0
        self.base_inst = {}
        self.days = 30
        self.instId = 'BTC-USDT-SWAP'
        self.bar = '1D'
        self.bar_df = pd.read_csv('{}/history_data/history_data_{}_{}.csv'.format(root_dir, self.instId, self.bar))
        self.money = 0
        self.cost = 0

    def strategy(self, ts):
        '''

        1. /api/v5/market/candles 获取k线 最近30天的最高价和最低价
        2. 可以根据收盘价算5日线 10日线 20日线
        3. 方法二：ws监控当前价格，如果破箱体，则开趋势仓，并设置止损为无利润点，初始-5*杠杆，如果到了10倍之后，且20日线大于无利润止损点，则每日将止损点太高至20线
        4. 监控成交，买入卖出要有日志
        5. 先写出来后面再做回测
        6. 做完了回测写网格
        {'code': '0', 'msg': '', 'data': [{'instType': 'SWAP', 'instId': 'BTC-USD-SWAP', 'last': '93432', 'lastSz': '571', 'askPx': '93431.4', 'askSz': '690', 'bidPx': '93431.3', 'bidSz': '779', 'open24h': '91624', 'high24h': '96227.8', 'low24h': '90169.7', 'volCcy24h': '12930.8081', 'vol24h': '11980205', 'ts': '1732707590910', 'sodUtc0': '91945.3', 'sodUtc8': '92812'}]}
        '''

        # 1. 获取当前币种是否由趋势仓，如果有判断是否更新，没有判断是否符合减仓环境
        # 1. 获取当前价格
        # self.bar_df.set_index('ts', inplace=True)
        self.bar_df['ts'] = self.bar_df['ts'].astype(str)

        self.current_value = self.bar_df.loc[self.bar_df['ts'] == ts, 'c'].tolist()[0]

        print(ts, self.current_value)
        # 获取近30个周期的极值 从ts往前数30个pd
        h, l = self.get_high_low(ts)

        file_name = 'testing_{}_{}.csv'.format(self.instId, self.bar)
        file_path = '{}/history_data/{}'.format(root_dir, file_name)

        testing_df = pd.read_csv(file_path)

        datetime_time = datetime.strptime(ts, "%Y-%m-%d")
        pre_obj = datetime_time - timedelta(days=2)
        pre = pre_obj.strftime("%Y-%m-%d")
        pre_ma5 = self.bar_df.loc[self.bar_df['ts'] == pre, 'ma5'].tolist()[0]
        pre_ma20 = self.bar_df.loc[self.bar_df['ts'] == pre, 'ma20'].tolist()[0]

        now_obj = datetime_time - timedelta(days=1)
        now = now_obj.strftime("%Y-%m-%d")
        ma5 = self.bar_df.loc[self.bar_df['ts'] == now, 'ma5'].tolist()[0]
        ma20 = self.bar_df.loc[self.bar_df['ts'] == now, 'ma20'].tolist()[0]


        # 查下单文件
        # 如果无持仓，则判断是否需要下单，如果有持仓判断是否需要平仓
        # 找到前一日的5,20均线和前2日的5,20均线

        if (pre_ma5 < pre_ma20) and (ma5 > ma20):
            if testing_df.shape[0] == 0:
                print('无记录下初始单--------------------')
                # ts,operate,value,num,remaining,all
                num = round(self.money / self.current_value, 2) - 0.01
                remaining = round(self.money - self.current_value * num, 2)
                all = round(remaining + self.current_value * num, 2)
                data = [[ts, 'b', self.current_value, num, remaining, all]]
                df = pd.DataFrame(data, columns=['ts', 'operate', 'value', 'num', 'remaining', 'all'])
                df.to_csv(file_path, index=False)
                self.order(data)
                self.cost = self.current_value
                operrate_date = [ts, 'b', self.current_value, num, remaining, all]
                self.order(operrate_date)
            elif testing_df.iloc[-1]['num'] == 0:
                # 此处未计算滑点以及手续费
                print('无持仓则下单--------------------')
                num = round(testing_df.iloc[-1]['all'] / self.current_value, 2) - 0.01
                remaining = round(testing_df.iloc[-1]['all'] - self.current_value * num, 2)
                all = round(remaining + self.current_value * num, 2)
                data = [ts, 'b', self.current_value, num, remaining, all]
                testing_df.loc[len(testing_df.index)] = data
                testing_df.to_csv(file_path, index=False)
                self.order(data)
                self.cost = self.current_value
            # elif testing_df.iloc[-1]['num'] != 0:
            #     # 有持仓不动
            #     print('有持仓则不动--------------------')
            #     all = round(testing_df.iloc[-1]['num']*self.current_value+testing_df.iloc[-1]['remaining'],2)
            #     data = [ts, 'o', self.current_value, testing_df.iloc[-1]['num'], testing_df.iloc[-1]['remaining'], all]
            #     testing_df.loc[len(testing_df.index)] = data
            #     testing_df.to_csv(file_path, index=False)
        elif (pre_ma5 > pre_ma20) and (ma5 < ma20):
            # 判断是否需要卖出并记录日志无操作或卖出
            if testing_df.shape[0] == 0:
                print('初始无操作')
                data = [[ts, 'o', self.current_value, 0, self.money, self.money]]
                df = pd.DataFrame(data, columns=['ts', 'operate', 'value', 'num', 'remaining', 'all'])
                df.to_csv(file_path, index=False)
            else:
                # todo 加o或者s
                if self.cost == 0:
                    # 已经无持仓
                    print('已无持仓')
                    data = [ts, 'o', self.current_value, 0, testing_df.iloc[-1]['remaining'], testing_df.iloc[-1]['all']]
                    testing_df.loc[len(testing_df.index)] = data
                    testing_df.to_csv(file_path, index=False)
                else:
                    # 割肉
                    print('卖出')
                    remaining = round(testing_df.iloc[-1]['remaining']+testing_df.iloc[-1]['num']*self.current_value,2)
                    data = [ts, 's', self.current_value, 0, remaining, remaining]
                    testing_df.loc[len(testing_df.index)] = data
                    testing_df.to_csv(file_path, index=False)
                    self.cost = 0
                    self.order(data)
                # elif 1==2:
                #     # 跌破20日均线卖出
                #     pass
        else:
            if testing_df.shape[0] == 0:
                print('初始无操作')
                data = [[ts, 'o', self.current_value, 0, self.money, self.money]]
                df = pd.DataFrame(data, columns=['ts', 'operate', 'value', 'num', 'remaining', 'all'])
                df.to_csv(file_path, index=False)
            else:
                # 不动
                print('不动')
                remaining = testing_df.iloc[-1]['remaining']
                all = round(remaining+self.current_value * testing_df.iloc[-1]['num'],2)
                data = [ts, 'o', self.current_value, testing_df.iloc[-1]['num'], remaining, all]
                testing_df.loc[len(testing_df.index)] = data
                testing_df.to_csv(file_path, index=False)


    def order(self, *args):
        print('下单', args)


    def get_high_low(self, ts):
        df = self.bar_df
        df_sorted_by_column = df.sort_values(by='ts', ascending=True)
        datetime_time = datetime.strptime(ts, "%Y-%m-%d")
        # 前一天到前30天最高最低
        after_obj = datetime_time - timedelta(days=1)
        after = after_obj.strftime("%Y-%m-%d")
        before_obj = datetime_time - timedelta(days=self.days)
        before = before_obj.strftime("%Y-%m-%d")
        df_days = df_sorted_by_column.loc[(df_sorted_by_column['ts'] <= after) & (df_sorted_by_column['ts'] >= before)]
        high = max(df_days['c'])
        low = min(df_days['c'])
        return high, low

    def get_positions(self):

        # 下单后记录csv文件
        res = {}
        print(res)
        return res


if __name__ == '__main__':
    pass
