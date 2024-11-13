'''
下单
 print(self.tradeApi.place_order("BTC-USDT-SWAP", tdMode="isolated", clOrdId="testbtcusdt01", side="buy", ordType="market",
                                        sz="0.6",posSide="long"))
 https://www.okx.com/docs-v5/zh/#order-book-trading-trade-post-place-order
'''


class BaseOrder:

    def __init__(self, base_inst_dict):
        self.base_inst_dict = base_inst_dict
        self.instId = base_inst_dict.get('instId')  # 产品ID，如 BTC-USDT
        self.tdMode = base_inst_dict.get('tdMode')  # 交易模式 保证金模式：isolated：逐仓 ；cross：全仓
        self.clOrdId = base_inst_dict.get('clOrdId')  # 客户自定义订单ID 字母（区分大小写）与数字的组合，可以是纯字母、纯数字且长度要在1-32位之间。
        self.side = base_inst_dict.get('side')  # buy：买， sell：卖
        self.ordType = base_inst_dict.get('ordType')  # 订单类型market：市价单 limit：限价单
        self.sz = base_inst_dict.get('sz')  # 委托数量
        self.posSide = base_inst_dict.get('posSide')  # 持仓方向 long：开平仓模式开多，pos为正 short：开平仓模式开空，pos为正
