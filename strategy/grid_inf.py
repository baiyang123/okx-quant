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
'''


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
                # todo 先检查是否和设置的杠杆符合，如果不符合则先设置杠杆
                level = strategy_config.get('level')  # 杠杆
                pos_direction = strategy_config.get('pos_direction')
                initial_position = strategy_config.get('initial_position')
                # 产品当前信息
                ticket_info = mf(flag).get_ticker_info_by_instId(instId)
                lotsz = af(flag).get_lotSz(strategy_class_name=strategy_class_name, instId=instId)
                current_value = round(float(ticket_info.get('last')), lotsz)
                grid_info = mf(flag).get_grid_info(strategy_class_name, instId)
                # 默认14个周期平均移动均值
                atr = grid_info.get('atr')
                file_path = config_in_operation_path.format(root_dir)
                # 网格上下买点 先获取之前是否有网格上下买点，如果有按照之前的加，没有初始化，如果有redis是最好的，直接放在redis里，没有使用全局变量或放在文件持久化
                if not os.path.exists(file_path):
                    with open(file_path, "w") as file:
                        df = pd.DataFrame(columns=GRID_INF_OPERATION_COLUMNS)
                        print(df)
                        df.to_csv(file_path, index=False)
                else:
                    df = pd.read_csv(file_path)
                    if df.shape[0] == 0 or df[df['instId'] == instId].shape[0] == 0:
                        buyp = current_value - atr
                        sellp = current_value + atr
                        data = [instId, buyp, sellp, 'no']
                        df.loc[len(df.index)] = data
                        df.to_csv(file_path, index=False)
                        logger.info('网格数据初始化，上下网为{}-{}'.format(sellp, buyp))
                    else:
                        df = df[df['instId'] == instId]
                        buyp = df.iloc[0].get('buyp')
                        sellp = df.iloc[0].get('sellp')
                        logger.info('读取网格数据，上下网为{}-{}'.format(sellp, buyp))
                # 读取当前币种持仓
                acc_res = af(flag).get_strategy_position(strategy_class_name=strategy_class_name, instId=instId)
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
                pos = False
                for map in acc_res['pos_res']:
                    if map.get('pos') != '0':
                        pos = True
                        break
                # 有持仓
                if pos:
                    pass
                # 无持仓
                else:
                    # ['instId', 'buyp', 'sellp', 'direction']
                    if float(ticket_info['last']) > float(grid_info['boll_info']['ub']):
                        # 双向或可空
                        if pos_direction in (1, 2):
                            # 底仓
                            if initial_position * acc_res.get('totalEq') > acc_res.get('availBal'):
                                logger.error('到达开空区域,但金额不足{}-{}'.format(initial_position * acc_res.get('totalEq'), acc_res.get('availBal')))
                                return False
                            else:
                                # 一币等于多少张看 GET /api/v5/public/instruments todo 此处分母要乘以产品ctVal 币和张的换算关系，下单中一张（小单位）为单位
                                num = round(strategy_config.get('initial_position') * acc_res.get('totalEq') * level / current_value, lotsz)
                                data['num'] = num
                                data['side'] = 'sell'
                                data['posSide'] = 'short'  # long开仓 short平仓
                                df.loc[df['instId'] == instId, 'direction'] = 'short'
                                df.to_csv(file_path, index=False)
                                # 下空单
                                res = tf(flag).order(data=data, strategy_class_name=strategy_class_name, instId=instId)
                                if res['code'] != '1':
                                    logger.info('到达开空区域,买入空头底仓{}份，当前价格{}'.format(num, current_value))
                                else:
                                    logger.error('到达开空区域,下单失败{}'.format(res))
                    else:
                        # 做多
                        pass
        except Exception as e:
            logger.error(traceback.format_exc())
        finally:
            return True


if __name__ == '__main__':
    GridInf().strategy()




