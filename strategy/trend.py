'''
思路：
1. 获取最近30天的最高最低价，取最高最最低价，且最后一天的最高最低价不能是最高最低价
2. 监测价格，突破后开仓3 5 10
3. 设置止损为无利润点，如果到了10倍之后，且20日线大于无利润止损点，则每日将止损点太高至20线
4. 要有买卖日志，发消息
'''
from okx import Trade
from schemas.base_model import BaseOrder


class trend:

    def __init__(self, base_dict):
        # 初始化趋势策略下单相关属性
        self.base_inst = BaseOrder(base_dict)
        # 初始化账号
        api_key = 'd759cf97-a1b3-40da-9c49-911629d7b3b6'
        api_secret_key = 'C8C89E3E0D6FA34530F1BBD2C33DFDBF'
        passphrase = ''
        self.tradeApi = Trade.TradeAPI(api_key, api_secret_key, passphrase, False, '0')

    def strategy(self):
        '''

        1. /api/v5/market/candles 获取k线 最近30天的最高价和最低价
        2. 可以根据收盘价算5日线 10日线 20日线
        3. 方法二：ws监控当前价格，如果破箱体，则开趋势仓，并设置止损为无利润点，初始-5*杠杆，如果到了10倍之后，且20日线大于无利润止损点，则每日将止损点太高至20线
        4. 监控成交，买入卖出要有日志
        5. 先写出来后面再做回测
        6. 做完了回测写网格
        '''

        pass

    def order(self):
        instId =  self.base_inst.instId
        tdMode = self.base_inst.tdMode
        clOrdId = self.base_inst.clOrdId
        side = self.base_inst.side
        ordType = self.base_inst.ordType
        sz = self.base_inst.sz
        posSide = self.base_inst.posSide
        self.tradeApi.place_order(instId, tdMode=tdMode, clOrdId=clOrdId, side=side,
                                  ordType=ordType,
                                  sz=sz, posSide=posSide)