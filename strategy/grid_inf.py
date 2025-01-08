'''
思路：
快慢均线上下穿透，并设置观察期，初版不加杠杆，只做多
'''
import os
import pathlib
import traceback
from datetime import datetime

import pandas as pd
from loguru import logger

from config import STRATEGY_CLASS_CONFIG, GRID_INF_OPERATION_COLUMNS
from factory.AccountFactory import AccountFactory as af
from factory.MarketFactory import MarketFactory as mf
from factory.TradeFactory import TradeFactory as tf

root_dir = pathlib.Path(__file__).resolve().parent.parent
config_in_operation_path = '{}/operation_data/gridInf.csv'

'''
===========================模拟实盘，双向无线网格=采用新的配置规则，支持一个策略配置多个不通品种，每个品种适配的周期不同======================================
STRATEGY_CLASS_CONFIG = {
    'GridInf': {
        'BTC-USDT-SWAP': {
            'instId': 'BTC-USDT-SWAP',
            'bar_unit': 'Dutc',
            'bar': 1,
            'boll_bar': 20,
            'atr_bar': 14,
            'ccy': 'USDT',
            'positionRatio': 0.8,
            'level': 5,
            'instType': 'SWAP',
            'stopLossRatio': 0.15,
            'interval': 10,
            'ordType': 'market',
            'flag': '1',
            'initial_position': 0.2,
            'grid_position': 0.05,
            'pos_direction': 2,  # 0做多1做空2双向
        }
    }
}
# todo 思考：无线网格如果一直涨会不会触发买点缺没有仓位了，这个要找到那个即充分利用仓位又有仓位的最佳平衡点
开多：买入开多（side 填写 buy； posSide 填写 long ）
开空：卖出开空（side 填写 sell； posSide 填写 short ）
平多：卖出平多（side 填写 sell；posSide 填写 long ）
平空：买入平空（side 填写 buy； posSide 填写 short ）
'''

# todo 无线网格如果沿着一个方向一直搞会导致仓位越来越极端，直到无仓或者满仓，这时要设置好上线布林线距离开仓点得位置，以谋求达到日均波动与布林线间距得最佳值
# 大多数时候是涨的情况最坏止损且为原始仓位止损，这样不会高位梭哈，如果需要重跑只需要抹掉运行时配置即可
class GridInf:

    def __init__(self):
        pass

    def strategy(self):
        # 根据类名（就是策略类型）获取策略包含的品种
        strategy_class_name = self.__class__.__name__
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            strategy_class_config = STRATEGY_CLASS_CONFIG.get(strategy_class_name)
            for instId, strategy_config in strategy_class_config.items():
                flag = strategy_config.get('flag')  # 虚拟盘
                lever = strategy_config.get('lever')  # 杠杆
                pos_direction = strategy_config.get('pos_direction')
                initial_position = strategy_config.get('initial_position')
                positionRatio = strategy_config.get('positionRatio')
                grid_position = strategy_config.get('grid_position')
                # 产品当前信息
                ticket_info = mf(flag).get_ticker_info_by_instId(instId)
                lotsz = af(flag).get_lotSz(strategy_class_name=strategy_class_name, instId=instId)
                current_value = round(float(ticket_info.get('last')), lotsz)
                stopLossRatio = float('-{}'.format(strategy_config.get('stopLossRatio')))
                grid_info = mf(flag).get_grid_info(strategy_class_name, instId)
                # 默认14个周期平均移动均值
                atr = grid_info.get('atr')
                file_path = config_in_operation_path.format(root_dir)
                # 读取当前币种持仓
                # 一币等于多少张看 GET /api/v5/public/instruments  此处分母要乘以产品ctVal 币和张的换算关系，下单中一张（小单位）为单位
                instrument = mf(flag).get_instruments(strategy_class_name, instId)
                ctVal = float(instrument.get('ctVal'))
                acc_res = af(flag).get_strategy_position(strategy_class_name=strategy_class_name, instId=instId)
                initial_num_new = round(initial_position * acc_res.get('availBal') * lever / (
                            current_value * ctVal), lotsz)
                grid_num_new = round(grid_position * acc_res.get('availBal') * lever / (
                            current_value * ctVal), lotsz)
                # 判断当前是否有仓位
                pos = False
                for map in acc_res['pos_res']:
                    if map.get('pos') != '0':
                        pos = True
                        break
                # 网格上下买点 先获取之前是否有网格上下买点，如果有按照之前的加，没有初始化，如果有redis是最好的，直接放在redis里，没有使用全局变量或放在文件持久化
                if not os.path.exists(file_path):
                    with open(file_path, "w") as file:
                        df = pd.DataFrame(columns=GRID_INF_OPERATION_COLUMNS)
                        df.to_csv(file_path, index=False)
                else:
                    df = pd.read_csv(file_path)
                    if df.shape[0] == 0 or df[df['instId'] == instId].shape[0] == 0:
                        buyp = round(current_value - atr, lotsz)
                        sellp = round(current_value + atr, lotsz)
                        # 如果有仓位 说明已有底仓，则去仓位得方向以及仓位作为初始化数据
                        if pos:
                            for pos_variety in acc_res.get('pos_res'):
                                if pos_variety.get('pos') != '0' and pos_variety.get('instId') == instId:
                                    df_data = [instId, buyp, sellp, pos_variety.get('posSide'), pos_variety.get('availPos'), grid_num_new]
                                    grid_num = grid_num_new
                                else:
                                    df_data = [instId, buyp, sellp, 'no', 0, 0]
                                    grid_num = 0
                        else:
                            df_data = [instId, buyp, sellp, 'no', 0, 0]
                        df.loc[len(df.index)] = df_data
                        df.to_csv(file_path, index=False)
                        logger.info('网格数据初始化，上下网为{}-{}'.format(sellp, buyp))
                        # 初始化先设置杠杆 /api/v5/account/set-leverage
                        af(flag).set_levelage(strategy_class_name=strategy_class_name, instId=instId)
                    else:
                        df = df[df['instId'] == instId]
                        buyp = df.iloc[0].get('buyp')
                        sellp = df.iloc[0].get('sellp')
                        initial_num = df.iloc[0].get('initial_num') if df.iloc[0].get('initial_num') != 0 else initial_num_new
                        grid_num = df.iloc[0].get('grid_num') if df.iloc[0].get('grid_num') != 0 else grid_num_new
                        df.loc[df['instId'] == instId, 'initial_num'] = initial_num
                        df.loc[df['instId'] == instId, 'grid_num'] = grid_num
                        logger.info('读取网格数据，上下网为{}-{}'.format(sellp, buyp))
                data = {
                        'ts': ts,
                        'current_value': current_value,
                        'all': round(acc_res.get('totalEq'), lotsz),
                        'ordType': strategy_config.get('ordType'),
                        'attachAlgoOrds': []
                    }
                # print(ticket_info)
                # print(grid_info)
                # print(acc_res)
                # 有持仓
                if pos:
                    for pos_variety in acc_res.get('pos_res'):
                        if pos_variety.get('pos') != '0':
                            orders = tf(flag).get_orders_pending(instId)
                            # 大于止损线市价全平 /api/v5/trade/close-position，先撤单
                            if float(pos_variety.get('uplRatio')) < stopLossRatio:
                                if len(orders) > 0:
                                    cacal_order_list = []
                                    for order in orders:
                                        ordId = order.get('ordId')
                                        req = {
                                            'instId': instId,
                                            'ordId': ordId
                                        }
                                        cacal_order_list.append(req)
                                    tf(flag).cancel_batch_order(cacal_order_list)
                                tf(flag).close_positions(instId=instId, posSide=pos_variety.get('posSide'))
                            # 有空单仓位
                            if pos_variety.get('posSide') == 'short' and pos_direction in (1, 2):
                                # 小于下线直接全部止盈
                                if float(ticket_info['last']) < float(grid_info['boll_info']['lb']):
                                    num = pos_variety.get('availPos')
                                    data['num'] = num
                                    data['side'] = 'buy'
                                    data['posSide'] = 'short'
                                    df.loc[df['instId'] == instId, 'direction'] = 'closesell'
                                    df.to_csv(file_path, index=False)
                                    # 平空单
                                    logger.info('到达开多区域,空单全部止盈反手{}份，当前价格{}'.format(num, current_value))
                                    tf(flag).order(data=data, strategy_class_name=strategy_class_name, instId=instId)
                                    # 撤销所有预埋单
                                    if len(orders) > 0:
                                        cacal_order_list = []
                                        for order in orders:
                                            ordId = order.get('ordId')
                                            req = {
                                                'instId': instId,
                                                'ordId': ordId
                                            }
                                            cacal_order_list.append(req)
                                        tf(flag).cancel_batch_order(cacal_order_list)
                                    # 重新拿仓位 这里暂时不在一次循环里拿 走递归容易出问题 todo 后续优化
                                    # self.strategy()
                                else:
                                    # 判断是否有未被消耗的上下网
                                    # 上下网都被吃掉了 或者网格减仓了
                                    if len(orders) == 0:
                                        # # 开空 就是卖空回头还得买回来
                                        data['num'] = grid_num
                                        data['side'] = 'sell'
                                        data['posSide'] = 'short'
                                        data['ordType'] = 'limit'
                                        data['px'] = sellp
                                        df.loc[df['instId'] == instId, 'direction'] = 'sell'
                                        df.to_csv(file_path, index=False)
                                        logger.info('预埋空单{}份，当前价格{}'.format(grid_num, current_value))
                                        tf(flag).order(data=data, strategy_class_name=strategy_class_name,
                                                             instId=instId)
                                        # 平空
                                        data['num'] = grid_num
                                        data['side'] = 'buy'
                                        data['posSide'] = 'short'
                                        data['ordType'] = 'limit'
                                        data['px'] = buyp
                                        df.loc[df['instId'] == instId, 'direction'] = 'closesell'
                                        df.to_csv(file_path, index=False)
                                        logger.info('预埋平空单{}份，当前价格{}'.format(grid_num, current_value))
                                        tf(flag).order(data=data, strategy_class_name=strategy_class_name,
                                                             instId=instId)
                                    if len(orders) == 1:
                                        if orders[0]["side"] == 'buy':  # 止盈成交
                                            logger.info('止盈成交空单{}份，当前价格{}，继续埋网'.format(grid_num, current_value))
                                            ordId = orders[0].get('ordId')
                                            buyp = round(buyp - atr, lotsz)
                                            sellp = round(sellp - atr, lotsz)
                                            df.loc[df['instId'] == instId, 'buyp'] = buyp
                                            df.loc[df['instId'] == instId, 'sellp'] = sellp
                                            df.to_csv(file_path, index=False)
                                            tf(flag).cancel_order(instId=instId, ordId=ordId)
                                            # LogProfit(account["Balance"]) # 记录盈亏值
                                        if orders[0]["side"] == 'sell':
                                            logger.info('网格加仓空单{}份，当前价格{}，继续埋网'.format(grid_num, current_value))
                                            ordId = orders[0].get('ordId')
                                            buyp = round(buyp + atr, lotsz)
                                            sellp = round(sellp + atr, lotsz)
                                            df.loc[df['instId'] == instId, 'buyp'] = buyp
                                            df.loc[df['instId'] == instId, 'sellp'] = sellp
                                            df.to_csv(file_path, index=False)
                                            tf(flag).cancel_order(instId=instId, ordId=ordId)
                                            # LogProfit(account["Balance"])
                            # 有多单仓位
                            elif pos_variety.get('posSide') == 'long' and pos_direction in (0, 2):
                                # 多单全部止盈反手
                                if float(ticket_info['last']) > float(grid_info['boll_info']['ub']):
                                    num = pos_variety.get('availPos')
                                    data['num'] = num
                                    data['side'] = 'sell'
                                    data['posSide'] = 'long'
                                    df.loc[df['instId'] == instId, 'direction'] = 'closebuy'
                                    df.to_csv(file_path, index=False)
                                    # 平多单
                                    logger.info('到达开空区域,多单全部止盈反手{}份，当前价格{}'.format(num, current_value))
                                    tf(flag).order(data=data, strategy_class_name=strategy_class_name,
                                                         instId=instId)
                                    # 撤销所有预埋单
                                    if len(orders) > 0:
                                        cacal_order_list = []
                                        for order in orders:
                                            ordId = order.get('ordId')
                                            req = {
                                                'instId': instId,
                                                'ordId': ordId
                                            }
                                            cacal_order_list.append(req)
                                        tf(flag).cancel_batch_order(cacal_order_list)
                                    # 重新拿仓位 todo 后续优化
                                    # self.strategy()
                                else:
                                    if len(orders) == 0:
                                        # # 开多
                                        data['num'] = grid_num
                                        data['side'] = 'buy'
                                        data['posSide'] = 'long'
                                        data['ordType'] = 'limit'
                                        data['px'] = buyp
                                        df.loc[df['instId'] == instId, 'direction'] = 'buy'
                                        df.to_csv(file_path, index=False)
                                        tf(flag).order(data=data, strategy_class_name=strategy_class_name,
                                                             instId=instId)
                                        logger.info('预埋多单{}份，当前价格{}'.format(grid_num, current_value))
                                        # 平多
                                        data['num'] = grid_num
                                        data['side'] = 'sell'
                                        data['posSide'] = 'long'
                                        data['ordType'] = 'limit'
                                        data['px'] = sellp
                                        df.loc[df['instId'] == instId, 'direction'] = 'closebuy'
                                        df.to_csv(file_path, index=False)
                                        logger.info('预埋平多单{}份，当前价格{}'.format(grid_num, current_value))
                                        tf(flag).order(data=data, strategy_class_name=strategy_class_name,
                                                       instId=instId)
                                    if len(orders) == 1:
                                        if orders[0]["side"] == 'buy':  # 止盈成交
                                            logger.info('止盈成交多单{}份，当前价格{}，继续埋网'.format(grid_num, current_value))
                                            ordId = orders[0].get('ordId')
                                            buyp = round(buyp + atr, lotsz)
                                            sellp = round(sellp + atr, lotsz)
                                            df.loc[df['instId'] == instId, 'buyp'] = buyp
                                            df.loc[df['instId'] == instId, 'sellp'] = sellp
                                            df.to_csv(file_path, index=False)
                                            tf(flag).cancel_order(instId=instId, ordId=ordId)
                                            # LogProfit(account["Balance"]) # 记录盈亏值
                                        if orders[0]["side"] == 'sell':
                                            logger.info('止损成交多单{}份，当前价格{}，继续埋网'.format(grid_num, current_value))
                                            ordId = orders[0].get('ordId')
                                            buyp = round(buyp - atr, lotsz)
                                            sellp = round(sellp - atr, lotsz)
                                            df.loc[df['instId'] == instId, 'buyp'] = buyp
                                            df.loc[df['instId'] == instId, 'sellp'] = sellp
                                            df.to_csv(file_path, index=False)
                                            tf(flag).cancel_order(instId=instId, ordId=ordId)
                                            # LogProfit(account["Balance"]) # 记录盈亏值
                # 无持仓
                else:
                    # 底仓
                    initial_num = round(initial_position * positionRatio * acc_res.get('availBal') * lever / (
                            current_value * ctVal), lotsz)
                    grid_num = round(grid_position * positionRatio * acc_res.get('availBal') * lever / (
                            current_value * ctVal), lotsz)
                    # 大于上线，为做空区间
                    if float(ticket_info['last']) > float(grid_info['boll_info']['ub']):
                        # 双向或可空
                        if pos_direction in (1, 2):
                            data['num'] = initial_num
                            data['side'] = 'sell'
                            data['posSide'] = 'short'
                            df.loc[df['instId'] == instId, 'direction'] = 'short'
                            df.loc[df['instId'] == instId, 'initial_num'] = initial_num
                            df.loc[df['instId'] == instId, 'grid_num'] = grid_num
                            df.to_csv(file_path, index=False)
                            # 下空单
                            logger.info('到达开空区域,买入空头底仓{}份，当前价格{}'.format(initial_num, current_value))
                            tf(flag).order(data=data, strategy_class_name=strategy_class_name, instId=instId)
                    else:
                        # 做多区间 这里可以让低于下布林线为做多区间，在布林线间观望
                        if pos_direction in (0, 2):
                            data['num'] = initial_num
                            data['side'] = 'buy'
                            data['posSide'] = 'long'
                            df.loc[df['instId'] == instId, 'direction'] = 'long'
                            df.loc[df['instId'] == instId, 'initial_num'] = initial_num
                            df.loc[df['instId'] == instId, 'grid_num'] = grid_num
                            df.to_csv(file_path, index=False)
                            # 下多单
                            logger.info('到达开多区域,买入多头底仓{}份，当前价格{}'.format(initial_num, current_value))
                            tf(flag).order(data=data, strategy_class_name=strategy_class_name, instId=instId)
        except Exception as e:
            logger.error(traceback.format_exc())
        finally:
            return True


if __name__ == '__main__':
    GridInf().strategy()




