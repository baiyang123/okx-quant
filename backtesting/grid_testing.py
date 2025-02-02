import json
import os
import pathlib
import traceback
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from loguru import logger

from config import STRATEGY_CLASS_CONFIG, GRID_INF_OPERATION_COLUMNS, COLUMNS, GRID_INF_OPERATION_COLUMNS_TESTING, \
    ORDER_PATH, ORDER_COLUMNS, ORDER_COLUMNS_TESTING, GRID_INF_OPERATION_HISTORY_TESTING
from factory.AccountFactory import AccountFactory as af
from factory.MarketFactory import MarketFactory as mf
from factory.TradeFactory import TradeFactory as tf
from strategy.grid_inf import config_in_operation_path

root_dir = pathlib.Path(__file__).resolve().parent.parent


# instId,buyp,sellp,direction,initial_num,grid_num 总收益为股票差价乘以数量成杠杆
# 网格先写的模拟盘，所以回测写的比较简单
# todo 将回测和模拟盘的公用方法通过flag的方式合并体系，例如order等方法
# 如果底仓不够网格仓位一直卖的话就会卖空，
# todo 这样要加一个校验，如果仓位小于一次网格仓位的话需要清仓重新开启新的一轮（也说明上下布尔和日均移动量计算的算法有瑕疵）， 同理如果一直止损成交爆了仓位也是不对的
class Grid_Testing:

    def __init__(self):
        self.pos = ['instId', 'buyp', 'sellp', 'direction', 'initial_num', 'grid_num', 'position', 'lbpos', 'lspos',
                    'sspos', 'sbpos', 'all', 'all_start']
        self.bar_df = ''
        self.current_value = 0  # 当前币种金额
        self.instId = 'BTC-USDT-SWAP'
        self.buyp = 0
        self.sellp = 0
        self.direction = 'no'
        self.initial_num = 0
        self.grid_num = 0
        self.position = 0
        self.lbpos = 0
        self.lspos = 0
        self.sspos = 0
        self.sbpos = 0
        self.all = 100000
        self.all_start = 100000
        self.remain = 100000
        self.flag = 1
        self.atr_bar = 14
        self.frequency = 1
        self.availBal = 100000

    def strategy(self, ts):
        print(ts)
        # 根据类名（就是策略类型）获取策略包含的品种
        strategy_class_name = self.__class__.__name__
        try:
            strategy_class_config = STRATEGY_CLASS_CONFIG.get(strategy_class_name)
            for instId, strategy_config in strategy_class_config.items():
                flag = strategy_config.get('flag')  # 虚拟盘
                lever = strategy_config.get('lever')  # 杠杆
                pos_direction = strategy_config.get('pos_direction')
                initial_position = strategy_config.get('initial_position')
                positionRatio = strategy_config.get('positionRatio')
                grid_position = strategy_config.get('grid_position')
                boll_bar = strategy_config.get('boll_bar')
                atr_bar = strategy_config.get('boll_bar')
                frequency = strategy_config.get('frequency')
                self.atr_bar = atr_bar
                self.frequency = frequency
                bar = strategy_config.get('bar')
                # 简化写法--------------------
                self.bar_df = pd.read_csv(
                    '{}/history_data/history_data_{}_{}D.csv'.format(root_dir, self.instId, bar))
                self.bar_df['ts'] = self.bar_df['ts'].astype(str)
                # df.to_json 很好用
                # {'ts': '2023-03-05', 'o': 22434.0, 'h': 22599.0, 'l': 22250.0, 'c': 22550.5, 'vol': 6460415.0, 'volCcy': 64604.15, 'volCcyQuote': 1448268050.8, 'confirm': 1, 'ma5': 0.0, 'ma20': 0.0}
                # <class 'dict'>
                # 产品当天详情
                ticket_info = json.loads(self.bar_df.loc[self.bar_df['ts'] == ts].to_json(orient='records'))[0]
                self.current_value = ticket_info.get('c')
                # 简化写法-------------------
                lotsz = 1
                current_value = round(float(self.current_value), lotsz)
                stopLossRatio = float('{}'.format(strategy_config.get('stopLossRatio')))
                # 根据self.bar_df算出当前ts的各项指标 这里先回测天
                ts_obj = datetime.strptime(ts, '%Y-%m-%d')
                before_datetime = ts_obj - timedelta(days=boll_bar)
                before_datetime_str = before_datetime.strftime('%Y-%m-%d')
                df_boll = self.bar_df[(self.bar_df['ts'] < ts) & (self.bar_df['ts'] >= before_datetime_str)]
                grid_info = self.get_grid_info(df_boll)
                # # 默认14个周期平均移动均值
                atr = grid_info.get('atr')
                file_path = '{}/operation_data/gridInf_testing.csv'.format(root_dir)
                # 读取当前币种持仓
                # 一币等于多少张看 GET /api/v5/public/instruments  此处分母要乘以产品ctVal 币和张的换算关系，下单中一张（小单位）为单位
                # instrument = mf(flag).get_instruments(strategy_class_name, instId)
                # 简化写法----------------------
                ctVal = float(0.01)
                # acc_res = self.get_strategy_position(strategy_class_name=strategy_class_name, instId=instId)
                initial_num_new = round(initial_position * self.availBal * lever / (
                        current_value * ctVal), lotsz)
                grid_num_new = round(grid_position * self.availBal * lever / (
                        current_value * ctVal), lotsz)
                # 判断当前是否有仓位
                pos = False
                # for map in acc_res['pos_res']:
                #     if map.get('pos') != '0':
                #         pos = True
                #         break

                # 网格上下买点 先获取之前是否有网格上下买点，如果有按照之前的加，没有初始化，如果有redis是最好的，直接放在redis里，没有使用全局变量或放在文件持久化
                if not os.path.exists(file_path):
                    with open(file_path, "w") as file:
                        df = pd.DataFrame(columns=GRID_INF_OPERATION_COLUMNS_TESTING)
                        df.to_csv(file_path, index=False)
                        all = self.all
                else:
                    df = pd.read_csv(file_path)
                    if df.shape[0] == 0 or df[df['instId'] == instId].shape[0] == 0:
                        buyp = round(current_value - atr, lotsz)
                        sellp = round(current_value + atr, lotsz)
                        # 如果有仓位 说明已有底仓，则去仓位得方向以及仓位作为初始化数据
                        # if pos:
                        #     for pos_variety in acc_res.get('pos_res'):
                        #         if pos_variety.get('pos') != '0' and pos_variety.get('instId') == instId:
                        #             df_data = [instId, buyp, sellp, pos_variety.get('posSide'),
                        #                        pos_variety.get('availPos'), grid_num_new]
                        #             grid_num = grid_num_new
                        #         else:
                        #             df_data = [instId, buyp, sellp, 'no', 0, 0]
                        #             grid_num = 0
                        # else:
                        # ['instId', 'buyp', 'sellp', 'direction', 'initial_num', 'grid_num', 'position', 'lbpos', 'lspos', 'sspos', 'sbpos', 'all', 'all_start']
                        df_data = [instId, buyp, sellp, 'no', 0, 0, 0, 0, 0, 0, 0, self.all, self.all, self.all, 0]
                        df.loc[len(df.index)] = df_data
                        df.to_csv(file_path, index=False)
                        logger.info('网格数据初始化，上下网为{}-{}'.format(sellp, buyp))
                        all = self.all

                        # 初始化先设置杠杆 /api/v5/account/set-leverage
                        # af(flag).set_levelage(strategy_class_name=strategy_class_name, instId=instId)
                    else:
                        df = df[df['instId'] == instId]
                        buyp = df.iloc[0].get('buyp')
                        sellp = df.iloc[0].get('sellp')
                        initial_num = df.iloc[0].get('initial_num') if df.iloc[0].get(
                            'initial_num') != 0 else initial_num_new
                        grid_num = df.iloc[0].get('grid_num') if df.iloc[0].get('grid_num') != 0 else grid_num_new
                        df.loc[df['instId'] == instId, 'initial_num'] = initial_num
                        df.loc[df['instId'] == instId, 'grid_num'] = grid_num
                        logger.info('读取网格数据，上下网为{}-{}'.format(sellp, buyp))
                        all = df.iloc[0].get('all')
                        self.buyp = df.iloc[0].get('buyp')
                        self.sellp = df.iloc[0].get('sellp')
                        self.direction = df.iloc[0].get('direction')
                        self.initial_num = df.iloc[0].get('initial_num')
                        self.grid_num = df.iloc[0].get('grid_num')
                        self.position = df.iloc[0].get('position')
                        self.lbpos = df.iloc[0].get('lbpos')
                        self.lspos = df.iloc[0].get('lspos')
                        self.sspos = df.iloc[0].get('sspos')
                        self.sbpos = df.iloc[0].get('sbpos')
                        self.all = df.iloc[0].get('all')
                        self.all_start = df.iloc[0].get('all_start')
                        self.remain = df.iloc[0].get('remain')
                        self.order_value = df.iloc[0].get('order_value')
                        print(buyp, sellp)
                data = {
                    'ts': ts,
                    'current_value': current_value,
                    'all': round(all, lotsz),
                    'ordType': strategy_config.get('ordType'),
                    'attachAlgoOrds': []
                }
                #  有持仓
                # instId,buyp,sellp,direction,initial_num,grid_num,position,lbpos,lspos,sspos,sbpos,all,all_start,remain
                # BTC-USDT-SWAP,55343.3,58426.7,long,28.1,7,28.1,0,0,0,0,100000,100000,84015.3
                if self.position != 0:
                    # for pos_variety in acc_res.get('pos_res'):
                    # if pos_variety.get('pos') != '0':
                    # orders = tf(flag).get_orders_pending(instId)
                    # 大于止损线市价全平 /api/v5/trade/close-position，先撤单
                    diff = float((self.order_value - current_value) / self.order_value)
                    if (self.direction == 'long' and stopLossRatio < -diff) or (self.direction == 'short' and stopLossRatio < -diff) or self.position < self.grid_num:
                        logger.info('亏损{}大于止损线市价全平，当前价格{}'.format(diff, current_value))
                        if self.lbpos != 0 or self.lspos != 0 or self.sspos != 0 or self.sbpos != 0:
                            # cacal_order_list = []
                            # for order in orders:
                            #     ordId = order.get('ordId')
                            #     req = {
                            #         'instId': instId,
                            #         'ordId': ordId
                            #     }
                            #     cacal_order_list.append(req)
                            # tf(flag).cancel_batch_order(cacal_order_list)
                            # 撤单
                            self.lbpos = 0
                            self.lspos = 0
                            self.sspos = 0
                            self.sbpos = 0
                            df.loc[df['instId'] == instId, 'lbpos'] = 0
                            df.loc[df['instId'] == instId, 'lspos'] = 0
                            df.loc[df['instId'] == instId, 'sspos'] = 0
                            df.loc[df['instId'] == instId, 'sbpos'] = 0
                        # 平仓
                        self.all = round(self.remain + self.position * current_value*ctVal / lever, lotsz)
                        df.loc[df['instId'] == instId, 'all_start'] = self.all
                        df.loc[df['instId'] == instId, 'all'] = self.all
                        df.loc[df['instId'] == instId, 'remain'] = self.all

                        df.loc[df['instId'] == instId, 'direction'] = 'no'
                        df.loc[df['instId'] == instId, 'position'] = 0

                        # df.loc[df['instId'] == instId, 'all_start'] = self.all_start - abs(
                        #     current_value - self.order_value) * self.position * ctVal * lever
                        # df.loc[df['instId'] == instId, 'all'] = self.all_start - abs(
                        #     current_value - self.order_value) * self.position * ctVal * lever
                        # df.loc[df['instId'] == instId, 'remain'] = self.all_start - abs(
                        #     current_value - self.order_value) * self.position * ctVal * lever

                        # tf(flag).close_positions(instId=instId, posSide=pos_variety.get('posSide'))
                        # 止损后本轮终止
                        df.to_csv(file_path, index=False)
                        return True
                    # 有空单仓位
                    if self.direction == 'short' and pos_direction in (1, 2):
                        # 小于下线直接全部止盈
                        if float(self.current_value) < float(grid_info['boll_info']['lb']):
                            num = self.position
                            data['num'] = num
                            data['side'] = 'buy'
                            data['posSide'] = 'short'
                            # df.loc[df['instId'] == instId, 'direction'] = 'no'
                            # df.to_csv(file_path, index=False)
                            # 平空单
                            logger.info('到达开多区域,空单全部止盈反手{}份，当前价格{}'.format(num, current_value))
                            # tf(flag).order(data=data, strategy_class_name=strategy_class_name, instId=instId)
                            df.loc[df['instId'] == instId, 'direction'] = 'no'
                            df.loc[df['instId'] == instId, 'position'] = 0
                            self.all = round(self.remain + num * current_value * ctVal / lever, lotsz)
                            df.loc[df['instId'] == instId, 'remain'] = self.all
                            df.loc[df['instId'] == instId, 'all'] = self.all
                            df.loc[df['instId'] == instId, 'all_start'] = self.all

                            # df.loc[df['instId'] == instId, 'all_start'] = self.all_start + abs(
                            #     current_value - self.order_value) * self.position * ctVal * lever
                            # df.loc[df['instId'] == instId, 'all'] = self.all_start + abs(
                            #     current_value - self.order_value) * self.position * ctVal * lever
                            # df.loc[df['instId'] == instId, 'remain'] = self.all_start + abs(
                            #     current_value - self.order_value) * self.position * ctVal * lever


                            self.order(data)
                            # 撤销所有预埋单
                            # if len(orders) > 0:
                            #     cacal_order_list = []
                            #     for order in orders:
                            #         ordId = order.get('ordId')
                            #         req = {
                            #             'instId': instId,
                            #             'ordId': ordId
                            #         }
                            #         cacal_order_list.append(req)
                            #     tf(flag).cancel_batch_order(cacal_order_list)
                            # 重新拿仓位 这里暂时不在一次循环里拿 走递归容易出问题 todo 后续优化
                            df.loc[df['instId'] == instId, 'lbpos'] = 0
                            df.loc[df['instId'] == instId, 'lspos'] = 0
                            df.loc[df['instId'] == instId, 'sspos'] = 0
                            df.loc[df['instId'] == instId, 'sbpos'] = 0
                            df.to_csv(file_path, index=False)
                            # self.strategy()
                        else:
                            # 判断是否有未被消耗的上下网
                            # 上下网都被吃掉了 或者网格减仓了,或者刚下底仓
                            if self.sbpos == 0 and self.sspos == 0:
                                # # 开空 就是卖空回头还得买回来
                                data['num'] = grid_num
                                data['side'] = 'sell'
                                data['posSide'] = 'short'
                                data['ordType'] = 'limit'
                                data['px'] = sellp
                                data['order_value'] = sellp
                                # df.loc[df['instId'] == instId, 'direction'] = 'sell'
                                df.loc[df['instId'] == instId, 'sspos'] = sellp
                                df.to_csv(file_path, index=False)
                                logger.info('预埋空单{}份{}，当前价格{}'.format(grid_num,sellp, current_value))
                                # tf(flag).order(data=data, strategy_class_name=strategy_class_name,
                                #                instId=instId)
                                self.order(data)
                                # 平空
                                data['num'] = grid_num
                                data['side'] = 'buy'
                                data['posSide'] = 'short'
                                data['ordType'] = 'limit'
                                data['px'] = buyp
                                data['order_value'] = buyp
                                # df.loc[df['instId'] == instId, 'direction'] = 'closesell'
                                df.loc[df['instId'] == instId, 'sbpos'] = buyp
                                df.to_csv(file_path, index=False)
                                logger.info('预埋平空单{}份{}，当前价格{}'.format(grid_num,buyp, current_value))
                                # tf(flag).order(data=data, strategy_class_name=strategy_class_name,
                                #                instId=instId)
                                self.order(data)
                            if current_value < buyp or current_value > sellp:
                                if current_value < buyp:  # 止盈成交
                                    logger.info('止盈成交空单{}份，当前价格{}，继续埋网'.format(grid_num, current_value))
                                    # ordId = orders[0].get('ordId')
                                    df.loc[df['instId'] == instId, 'lbpos'] = 0
                                    df.loc[df['instId'] == instId, 'lspos'] = 0
                                    df.loc[df['instId'] == instId, 'sspos'] = 0
                                    df.loc[df['instId'] == instId, 'sbpos'] = 0
                                    df.loc[df['instId'] == instId, 'position'] = self.position - grid_num
                                    df.loc[df['instId'] == instId, 'remain'] = round(self.remain+sellp*self.grid_num*ctVal / lever, lotsz)
                                    self.all = round(self.remain+sellp*self.grid_num*ctVal / lever + (self.position - grid_num)*current_value*ctVal / lever, lotsz)
                                    df.loc[df['instId'] == instId, 'all'] = self.all

                                    # df.loc[df['instId'] == instId, 'remain'] = round(self.remain+sellp*self.grid_num*ctVal / lever, lotsz) + abs(sellp - self.order_value) * grid_num * ctVal * lever
                                    # df.loc[df['instId'] == instId, 'all'] = self.all_start + abs(sellp - self.order_value) * grid_num * ctVal * lever

                                    buyp = round(buyp - atr, lotsz)
                                    sellp = round(sellp - atr, lotsz)
                                    df.loc[df['instId'] == instId, 'buyp'] = buyp
                                    df.loc[df['instId'] == instId, 'sellp'] = sellp
                                    df.to_csv(file_path, index=False)
                                    # tf(flag).cancel_order(instId=instId, ordId=ordId)
                                    # LogProfit(account["Balance"]) # 记录盈亏值
                                if current_value > sellp:
                                    logger.info('网格加仓空单{}份，当前价格{}，继续埋网'.format(grid_num, current_value))
                                    # ordId = orders[0].get('ordId')
                                    df.loc[df['instId'] == instId, 'lbpos'] = 0
                                    df.loc[df['instId'] == instId, 'lspos'] = 0
                                    df.loc[df['instId'] == instId, 'sspos'] = 0
                                    df.loc[df['instId'] == instId, 'sbpos'] = 0
                                    df.loc[df['instId'] == instId, 'position'] = self.position + grid_num
                                    df.loc[df['instId'] == instId, 'remain'] = round(self.remain - buyp*self.grid_num*ctVal / lever, lotsz)
                                    self.all = round(self.remain - buyp*self.grid_num*ctVal / lever + (
                                                self.position + grid_num) * current_value*ctVal / lever, lotsz)
                                    df.loc[df['instId'] == instId, 'all'] = self.all

                                    buyp = round(buyp + atr, lotsz)
                                    sellp = round(sellp + atr, lotsz)
                                    df.loc[df['instId'] == instId, 'buyp'] = buyp
                                    df.loc[df['instId'] == instId, 'sellp'] = sellp
                                    df.to_csv(file_path, index=False)
                                    # tf(flag).cancel_order(instId=instId, ordId=ordId)
                                    # LogProfit(account["Balance"])
                    # 有多单仓位
                    elif self.direction == 'long' and pos_direction in (0, 2):
                        # 多单全部止盈反手
                        if float(self.current_value) > float(grid_info['boll_info']['ub']):
                            num = self.position
                            data['num'] = num
                            data['side'] = 'sell'
                            data['posSide'] = 'long'
                            # df.loc[df['instId'] == instId, 'direction'] = 'closebuy'
                            # df.to_csv(file_path, index=False)
                            # 平多单
                            logger.info('到达开空区域,多单全部止盈反手{}份，当前价格{}'.format(num, current_value))
                            # tf(flag).order(data=data, strategy_class_name=strategy_class_name,
                            #                instId=instId)
                            df.loc[df['instId'] == instId, 'direction'] = 'no'
                            df.loc[df['instId'] == instId, 'position'] = 0
                            self.all = round(self.remain + num * current_value*ctVal / lever, lotsz)
                            df.loc[df['instId'] == instId, 'remain'] = self.all
                            df.loc[df['instId'] == instId, 'all'] = self.all
                            df.loc[df['instId'] == instId, 'all_start'] = self.all


                            # df.loc[df['instId'] == instId, 'all_start'] = self.all_start + abs(
                            #     current_value - self.order_value) * self.position * ctVal * lever
                            # df.loc[df['instId'] == instId, 'all'] = self.all_start + abs(
                            #     current_value - self.order_value) * self.position * ctVal * lever
                            # df.loc[df['instId'] == instId, 'remain'] = self.all_start + abs(
                            #     current_value - self.order_value) * self.position * ctVal * lever

                            self.order(data)
                            # 撤销所有预埋单
                            # if len(orders) > 0:
                            #     cacal_order_list = []
                            #     for order in orders:
                            #         ordId = order.get('ordId')
                            #         req = {
                            #             'instId': instId,
                            #             'ordId': ordId
                            #         }
                            #         cacal_order_list.append(req)
                            #     tf(flag).cancel_batch_order(cacal_order_list)
                            # self.lbpos != 0 or self.lspos != 0 or self.sspos != 0 or self.sbpos != 0
                            df.loc[df['instId'] == instId, 'lbpos'] = 0
                            df.loc[df['instId'] == instId, 'lspos'] = 0
                            df.loc[df['instId'] == instId, 'sspos'] = 0
                            df.loc[df['instId'] == instId, 'sbpos'] = 0
                            df.to_csv(file_path, index=False)
                            # 重新拿仓位 todo 后续优化
                            # self.strategy()
                        else:
                            # if len(orders) == 0:
                            if self.lbpos == 0 and self.lspos == 0:
                                # # 开多
                                data['num'] = grid_num
                                data['side'] = 'buy'
                                data['posSide'] = 'long'
                                data['ordType'] = 'limit'
                                data['px'] = buyp
                                data['order_value'] = buyp
                                # df.loc[df['instId'] == instId, 'direction'] = 'long'
                                df.loc[df['instId'] == instId, 'lbpos'] = buyp
                                df.to_csv(file_path, index=False)
                                # tf(flag).order(data=data, strategy_class_name=strategy_class_name,
                                #                instId=instId)
                                self.order(data)
                                logger.info('预埋多单{}份，当前价格{}'.format(grid_num, current_value))
                                # 平多
                                data['num'] = grid_num
                                data['side'] = 'sell'
                                data['posSide'] = 'long'
                                data['ordType'] = 'limit'
                                data['px'] = sellp
                                data['order_value'] = sellp
                                # df.loc[df['instId'] == instId, 'direction'] = 'long'
                                df.loc[df['instId'] == instId, 'lspos'] = sellp
                                df.to_csv(file_path, index=False)
                                logger.info('预埋平多单{}份，当前价格{}'.format(grid_num, current_value))
                                # tf(flag).order(data=data, strategy_class_name=strategy_class_name,
                                #                instId=instId)
                                self.order(data)
                            # if len(orders) == 1:
                            if current_value < buyp or current_value > sellp:
                                # if orders[0]["side"] == 'buy':  # 止盈成交
                                if current_value > sellp:
                                    logger.info('止盈成交多单{}份，当前价格{}，继续埋网'.format(grid_num, current_value))
                                    # ordId = orders[0].get('ordId')
                                    df.loc[df['instId'] == instId, 'lbpos'] = 0
                                    df.loc[df['instId'] == instId, 'lspos'] = 0
                                    df.loc[df['instId'] == instId, 'sspos'] = 0
                                    df.loc[df['instId'] == instId, 'sbpos'] = 0
                                    df.loc[df['instId'] == instId, 'position'] = self.position-grid_num
                                    df.loc[df['instId'] == instId, 'remain'] = round(self.remain + sellp*self.grid_num*ctVal / lever, lotsz)
                                    self.all = round(self.remain + sellp*self.grid_num*ctVal / lever + (
                                                self.position - grid_num) * current_value*ctVal / lever, lotsz)
                                    df.loc[df['instId'] == instId, 'all'] = self.all

                                    # df.loc[df['instId'] == instId, 'remain'] = round(
                                    #     self.remain + sellp * self.grid_num * ctVal / lever, lotsz) + abs(
                                    #     sellp - self.order_value) * grid_num * ctVal * lever
                                    # df.loc[df['instId'] == instId, 'all'] = self.all_start + abs(
                                    #     sellp - self.order_value) * grid_num * ctVal * lever

                                    buyp = round(buyp + atr, lotsz)
                                    sellp = round(sellp + atr, lotsz)
                                    df.loc[df['instId'] == instId, 'buyp'] = buyp
                                    df.loc[df['instId'] == instId, 'sellp'] = sellp
                                    df.to_csv(file_path, index=False)
                                    # tf(flag).cancel_order(instId=instId, ordId=ordId)
                                    # LogProfit(account["Balance"]) # 记录盈亏值
                                if current_value < buyp:
                                    logger.info('止损成交多单{}份，当前价格{}，继续埋网'.format(grid_num, current_value))
                                    # ordId = orders[0].get('ordId')

                                    df.loc[df['instId'] == instId, 'lbpos'] = 0
                                    df.loc[df['instId'] == instId, 'lspos'] = 0
                                    df.loc[df['instId'] == instId, 'sspos'] = 0
                                    df.loc[df['instId'] == instId, 'sbpos'] = 0
                                    df.loc[df['instId'] == instId, 'position'] = self.position + grid_num
                                    df.loc[df['instId'] == instId, 'remain'] = round(self.remain - buyp*self.grid_num*ctVal / lever, lotsz)
                                    self.all = round(self.remain - buyp*self.grid_num*ctVal / lever + (
                                            self.position + grid_num) * current_value*ctVal / lever, lotsz)
                                    df.loc[df['instId'] == instId, 'all'] = self.all
                                    buyp = round(buyp - atr, lotsz)
                                    sellp = round(sellp - atr, lotsz)
                                    df.loc[df['instId'] == instId, 'buyp'] = buyp
                                    df.loc[df['instId'] == instId, 'sellp'] = sellp
                                    df.to_csv(file_path, index=False)
                                    # tf(flag).cancel_order(instId=instId, ordId=ordId)
                                    # LogProfit(account["Balance"]) # 记录盈亏值
                # 无持仓
                else:
                    # 底仓
                    initial_num = round(initial_position * positionRatio * self.all_start * lever / (
                            current_value * ctVal), lotsz)
                    grid_num = round(grid_position * positionRatio * self.all_start * lever / (
                            current_value * ctVal), lotsz)
                    # 大于上线，为做空区间
                    if float(self.current_value) > float(grid_info['boll_info']['ub']):
                        # 双向或可空
                        if pos_direction in (1, 2):
                            data['num'] = initial_num
                            data['side'] = 'sell'
                            data['posSide'] = 'short'
                            df.loc[df['instId'] == instId, 'direction'] = 'short'
                            df.loc[df['instId'] == instId, 'initial_num'] = initial_num
                            df.loc[df['instId'] == instId, 'grid_num'] = grid_num
                            df.loc[df['instId'] == instId, 'remain'] = round(all - initial_num * current_value * ctVal / lever, lotsz)
                            df.loc[df['instId'] == instId, 'position'] = initial_num
                            df.loc[df['instId'] == instId, 'all'] = all
                            df.loc[df['instId'] == instId, 'order_value'] = current_value
                            df.to_csv(file_path, index=False)
                            # 下空单
                            logger.info('到达开空区域,买入空头底仓{}份，当前价格{}'.format(initial_num, current_value))
                            # tf(flag).order(data=data, strategy_class_name=strategy_class_name, instId=instId)
                            self.order(data)
                    else:
                        # 做多区间 这里可以让低于下布林线为做多区间，在布林线间观望
                        if pos_direction in (0, 2):
                            data['num'] = initial_num
                            data['side'] = 'buy'
                            data['posSide'] = 'long'
                            df.loc[df['instId'] == instId, 'direction'] = 'long'
                            df.loc[df['instId'] == instId, 'initial_num'] = initial_num
                            df.loc[df['instId'] == instId, 'grid_num'] = grid_num
                            df.loc[df['instId'] == instId, 'remain'] = round(all - initial_num * current_value * ctVal / lever, lotsz)
                            df.loc[df['instId'] == instId, 'position'] = initial_num
                            df.loc[df['instId'] == instId, 'all'] = all
                            df.loc[df['instId'] == instId, 'order_value'] = current_value
                            df.to_csv(file_path, index=False)
                            # 下多单
                            logger.info('到达开多区域,买入多头底仓{}份，当前价格{}'.format(initial_num, current_value))
                            # tf(flag).order(data=data, strategy_class_name=strategy_class_name, instId=instId)
                            self.order(data)
        except Exception as e:
            logger.error(traceback.format_exc())
        finally:
            file_path_history = '{}/history_data/testing/gridInf_testing.csv'.format(root_dir)
            # all的算法不对，缺少杠杆算法
            # all = round(float(df.iloc[0].get('position'))*float(current_value)*ctVal/lever + float(df.iloc[0].get('remain')), lotsz)
            all = self.all
            df = pd.read_csv(file_path)
            df.loc[df['instId'] == instId, 'all'] = all
            df.to_csv(file_path, index=False)
            df_h = pd.read_csv(file_path_history)
            df.iloc[0].get('position')
            df_h_new = [ts,
                        df.iloc[0].get('instId'),
                        df.iloc[0].get('buyp'),
                        df.iloc[0].get('sellp'),
                        df.iloc[0].get('direction'),
                        df.iloc[0].get('initial_num'),
                        df.iloc[0].get('grid_num'),
                        df.iloc[0].get('position'),
                        df.iloc[0].get('lbpos'),
                        df.iloc[0].get('lspos'),
                        df.iloc[0].get('sspos'),
                        df.iloc[0].get('sbpos'),
                        df.iloc[0].get('all'),
                        df.iloc[0].get('all_start'),
                        df.iloc[0].get('remain'),
                        current_value]
            df_h.loc[len(df_h.index)] = df_h_new
            # ts,instId,buyp,sellp,direction,initial_num,grid_num,position,lbpos,lspos,sspos,sbpos,all,all_start,remain
            df_h.to_csv(file_path_history, index=False)
            return True

    def order(self, data):
        ts = data.get('ts')
        current_value = data.get('current_value')
        all = data.get('all')
        side = data.get('side')
        posSide = data.get('posSide')
        num = data.get('num')
        ordType = data.get('ordType')
        attachAlgoOrds = data.get('attachAlgoOrds')
        px = data.get('px')
        file_name = 'BTC-USDT-SWAP_1D_testing.csv'
        file_path = ORDER_PATH.format(root_dir, file_name)
        if not os.path.exists(file_path):
            with open(file_path, "w") as file:
                df = pd.DataFrame(columns=ORDER_COLUMNS_TESTING)
                df.to_csv(file_path, index=False)

        order_df = pd.read_csv(file_path)
        loc = len(order_df.index)
        # todo这里可以继续添加发送邮箱等操作
        if px:
            order_value = px
        else:
            order_value = current_value
        data_loc = [ts, loc, side, posSide, order_value, current_value, num, all]
        order_df.loc[loc] = data_loc
        order_df.to_csv(file_path, index=False)
        logger.info(data)

    def get_grid_info(self, df_boll):
        df = pd.DataFrame(df_boll, columns=COLUMNS)
        df['c'] = df['c'].astype(float)
        df['h'] = df['h'].astype(float)
        df['l'] = df['l'].astype(float)
        # boll中线
        ma = df['c'].mean()
        data_set = np.array(df['c'])
        # 标准差
        standard_deviation = np.std(data_set)
        # 上下轨
        ub = ma + 2 * standard_deviation
        lb = ma - 2 * standard_deviation
        # 14日平均波动，最新一天不算
        df_atr = df.iloc[1: self.atr_bar]
        atr = (df_atr['h'] - df_atr['l']).mean()
        # 简化写法 --------------------------
        lotsz = 1
        result = {
            'boll_info': {
                'ma': round(ma, lotsz),
                'ub': round(ub, lotsz),
                'lb': round(lb, lotsz),
            },
            'atr': round(atr / (self.frequency * 2), lotsz)  # 一天的震荡除以二上下各一半，允许一天触碰一次网格，可根据想要的频率改变
        }
        return result

    def get_ticker_info_by_instId(self, instId):
        pass

    def get_strategy_position(self, strategy_class_name, instId):
        pass


if __name__ == '__main__':
    file_path = '{}/history_data/testing/gridInf_testing.csv'.format(root_dir)
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            df = pd.DataFrame(columns=GRID_INF_OPERATION_HISTORY_TESTING)
            df.to_csv(file_path, index=False)
    else:
        df = pd.DataFrame(columns=GRID_INF_OPERATION_HISTORY_TESTING)
        df.to_csv(file_path, index=False)

    # date_format = "%Y-%m-%d"
    start_time = '2023-04-30'
    end_time = '2024-10-30'
    while start_time <= end_time:
        Grid_Testing().strategy(start_time)
        next_time_obj = datetime.strptime(start_time, '%Y-%m-%d') + timedelta(days=1)
        start_time = datetime.strftime(next_time_obj, '%Y-%m-%d')
    df_all = pd.read_csv(file_path)
    value_start = df_all.loc[0]['current_value']
    all_start = df_all.loc[0]['all']
    from matplotlib import pyplot as plt

    fig, ax = plt.subplots()
    plt.plot(pd.to_datetime(df_all['ts']), round(df_all['all'] / all_start, 2), label='all')
    plt.plot(pd.to_datetime(df_all['ts']), round(df_all['current_value'] / value_start, 2), label='current_value')
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
    # 相关系数
    correlation = df_all['all'].corr(df_all['current_value'])
    logger.info('相关系数为{}'.format(correlation))
    # 计算最大回撤
    # 计算累计最大值
    cumulative_max_all = df_all['all'].cummax()
    cumulative_max_target = df_all['current_value'].cummax()
    # 计算每个点的回撤
    drawdowns_all = (df_all['all'] - cumulative_max_all) / cumulative_max_all
    drawdowns_target = (df_all['current_value'] - cumulative_max_target) / cumulative_max_target
    # 找出最大回撤
    max_drawdown_all = drawdowns_all.min()
    max_drawdown_target = drawdowns_target.min()
    logger.info('最大回撤分别为目标{}，策略{}'.format(max_drawdown_target, max_drawdown_all))

