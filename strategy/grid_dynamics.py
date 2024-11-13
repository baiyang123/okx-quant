'''
思路：
网格上下网必须涵盖强平线默认做多 破了30就更新网格（上破做多下破做空），不破就继续
'''
from flask import current_app

from okx import Grid
# rom schemas.base_model import BaseOrder
from factory.MarketFactory import MarketFactory as mf
from config import PASSPHRASE


class contract_grid:

    def __init__(self):
        # 初始化趋势策略下单相关属性
        # 初始化账号

        api_key = 'd759cf97-a1b3-40da-9c49-911629d7b3b6'
        api_secret_key = 'C8C89E3E0D6FA34530F1BBD2C33DFDBF'
        passphrase = PASSPHRASE
        self.GridAPI = Grid.GridAPI(api_key, api_secret_key, passphrase, False, '0')
        self.instId = 'BTC-USDT-SWAP'

    def strategy(self):
        # 获取n日线最高最低价格以及atr
        res, msg, data = mf().get_grid_box()
        print(res, msg, data)
        # 先查目前的网格委托单，如果没有则直接下单，如果高低有变化则根据高低进行切换多空网格然后现平仓再下单
        # 下网格单
        res = self.order()
        print(res)
        if res.get('code') == '0':
            return True, []
        else:
            return False, res.get('data')

    # https://www.okx.com/docs-v5/zh/?shell#order-book-trading-grid-trading-post-place-grid-algo-order
    '''
     def grid_order_algo(self, instId='', algoOrdType='', maxPx='', minPx='', gridNum='', runType='', tpTriggerPx='',
                        slTriggerPx='', tag='', quoteSz='', baseSz='', sz='', direction='', lever='', basePos=''):
        params = {'instId': instId, 'algoOrdType': algoOrdType, 'maxPx': maxPx, 'minPx': minPx, 'gridNum': gridNum,
                  'runType': runType, 'tpTriggerPx': tpTriggerPx, 'slTriggerPx': slTriggerPx, 'tag': tag,
                  'quoteSz': quoteSz, 'baseSz': baseSz, 'sz': sz, 'direction': direction, 'lever': lever,
                  'basePos': basePos}
    '''

    def order(self):
        # 下网格单
        res = self.GridAPI.grid_order_algo(self.instId, "contract_grid", "45000", "20000", "100", "1", sz='3000',
                                           direction='long', lever='3.0')
        # {'code': '1', 'data': [{'algoClOrdId': '', 'algoId': '', 'sCode': '51008', 'sMsg': 'Order failed.
        # Insufficient account balance.', 'tag': ''}], 'msg': ''}
        return res



'''
    self.instId = base_inst_dict.get('instId')  # 产品ID，如 BTC-USDT
    self.tdMode = base_inst_dict.get('tdMode')  # 交易模式 保证金模式：isolated：逐仓 ；cross：全仓
    self.clOrdId = base_inst_dict.get('clOrdId')  # 客户自定义订单ID 字母（区分大小写）与数字的组合，可以是纯字母、纯数字且长度要在1-32位之间。
    self.side = base_inst_dict.get('side')  # buy：买， sell：卖
    self.ordType = base_inst_dict.get('ordType')  # 订单类型market：市价单 limit：限价单
    self.sz = base_inst_dict.get('sz')  # 委托数量
    self.posSide = base_inst_dict.get('posSide')  # 持仓方向 long：开平仓模式开多，pos为正 short：开平仓模式开空，pos为正
'''


# 定时任务
def contract_grid_work(*args):
    print('work', args[0])
    contract_grid().strategy()
    pass


if __name__ == '__main__':
    contract_grid().strategy()
