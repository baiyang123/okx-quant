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
from factory.MarketFactory import MarketFactory
from okx import Trade,MarketData,Account
from schemas.base_model import BaseOrder

root_dir = pathlib.Path(__file__).resolve().parent.parent

class trend:

    def __init__(self):
        # 初始化趋势策略下单相关属性
        # self.base_inst = BaseOrder(base_dict)
        # 初始化账号
        api_key = 'd759cf97-a1b3-40da-9c49-911629d7b3b6'
        api_secret_key = 'C8C89E3E0D6FA34530F1BBD2C33DFDBF'
        passphrase = ''
        self.tradeApi = Trade.TradeAPI(api_key, api_secret_key, passphrase, False, '0')
        self.marketApi = MarketData.MarketAPI(api_key, api_secret_key, passphrase, False, '0')
        self.accountAPI = Account.AccountAPI(api_key, api_secret_key, passphrase, False, '0')
        self.current_ts = ''
        self.current_value = 0
        self.is_testing = False
        self.base_inst = {}
        self.days = 30
        self.instId = 'BTC-USDT-SWAP'
        self.bar = '1D'
        self.bar_df = pd.read_csv('{}/history_data/history_data_{}_{}.csv'.format(root_dir, self.instId,  self.bar))

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

        # 当天数据直接req最新数据
        res = self.marketApi.get_ticker('BTC-USD-SWAP')
        self.current_value = res['data'][0].get('last')


        print(ts, self.current_value)
        # 获取近30个周期的极值 从ts往前数30个pd
        h, l = self.get_high_low(ts)

        # 无持仓则下单


        # 查持仓
        # 获取当前持仓 本类型的 当前设定杠杆的(开始只做单方向)
        res_get_positions = self.get_positions()
        if not res_get_positions.get('posSide'):
            print('下单')
            if self.current_value > h:
                # 判断目前是否有当前类型的单 同样杠杆，方向，品种
                # todo 写公用方法log操作 切记录日志的时候需要写一个df文件，每个ts的收益情况，方便计算收益
                # 下多单
                self.order()
            else:
                # 检查是否需要清仓
                pass


        # 返回本次操作，时间



    def order(self):
        print('下单')
        # instId = self.base_inst.instId
        # tdMode = self.base_inst.tdMode
        # clOrdId = self.base_inst.clOrdId
        # side = self.base_inst.side
        # ordType = self.base_inst.ordType
        # sz = self.base_inst.sz
        # posSide = self.base_inst.posSide
        # self.tradeApi.place_order(instId, tdMode=tdMode, clOrdId=clOrdId, side=side,
        #                           ordType=ordType,
        #                           sz=sz, posSide=posSide)

    def get_high_low(self, ts):
        df = self.bar_df
        df_sorted_by_column = df.sort_values(by='ts', ascending=True)
        datetime_time = datetime.strptime(ts, "%Y-%m-%d")
        before_obj = datetime_time - timedelta(days=self.days)
        before = before_obj.strftime("%Y-%m-%d")
        df_days = df_sorted_by_column.loc[(df_sorted_by_column['ts'] <= ts) & (df_sorted_by_column['ts'] >= before)]
        high = max(df_days['c'])
        low = min(df_days['c'])
        return high, low

    def get_positions(self):
        if not self.is_testing:
            res = self.accountAPI.get_positions(self.instId)
        else:
            # 下单后记录csv文件
            res = {}
        print(res)
        return res


    # 三个定时任务,1. 更新周期内的值，2. 并且跑一遍策略 3. 定时任务计算前一天以及总收益 再可以有总定时任务计算总收益
def trend_work(*args):
    print('work', args[0])
    instId = trend().instId
    now = datetime.now()
    before = now - timedelta(days=trend().days)
    before = before.strftime("%Y-%m-%d")
    after = now.strftime("%Y-%m-%d")
    bar = trend().bar
    res, msg, income, percentage = MarketFactory().get_history_data(instId, before, after, bar)
    trend().strategy(now.strftime("%Y-%m-%d"))
    pass


if __name__ == '__main__':
    pass
