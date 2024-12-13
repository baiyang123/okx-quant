'''
思路：
快慢均线上下穿透，并设置观察期，初版不加杠杆，只做多
'''
import pathlib
import traceback
from datetime import datetime

from loguru import logger

from config import STRATEGY_CONFIG
from factory.AccountFactory import AccountFactory as af
from factory.MarketFactory import MarketFactory as mf
from factory.TradeFactory import TradeFactory as tf

root_dir = pathlib.Path(__file__).resolve().parent.parent

'''
===========================实盘慎用.在观摩了git回测代码后手敲的实现方案,暂时只带杠杆做多=======================================
'''


class moving:

    def __init__(self, db_session=None, context=None):
        # with context:
        #     super().__init__(db_session, context)
        #     self.app_context = context
        self.STATE_IDLE = -1  # -1空仓。long，short 暂时未启用
        self.strategy_code = 'BTC-USDT-SWAP_MA'

    def strategy(self):
        # 补try catch
        # with self.app_context:
        #     pass
        try:
            strategy_config = STRATEGY_CONFIG.get(self.strategy_code)
            if strategy_config is None:
                logger.error('{}策略未配置'.format(self.strategy_code))
                return False
            state = self.STATE_IDLE
            # 算快慢线（高频低频都可以现查）
            fl_res = mf().get_fast_low_ma(self.strategy_code)
            # {'pre_fp': 98701.68, 'pre_sp': 97341.78, 'pre_efp': 98701.68, 'pre_esp': 97341.78, 'fp': 98860.36,
            # 'sp': 97435.88, 'efp': 98860.36, 'esp': 97435.88, 'c': 100532.9}

            pre_fastPeriod = fl_res.get('pre_fp')
            pre_slowPeriod = fl_res.get('pre_sp')
            fastPeriod = fl_res.get('fp')
            slowPeriod = fl_res.get('sp')

            pre_exitFastPeriod = fl_res.get('pre_efp')
            pre_exitSlowPeriod = fl_res.get('pre_esp')
            exitFastPeriod = fl_res.get('efp')
            exitSlowPeriod = fl_res.get('esp')

            # 获取账户当前策略币种持仓以及可用金额（总金额以及配置的仓位）
            acc_res = af().get_strategy_position(self.strategy_code)
            positionRatio = strategy_config.get('positionRatio')
            level = strategy_config.get('level')
            stopLossRatio = strategy_config.get('stopLossRatio')
            ts =datetime.now().strftime("%Y-%m-%d")

            # 获取最小下单份额
            round_int = af().get_lotSz(self.strategy_code)

            # 获取产品信息
            ticket_info = mf().get_ticker_info(self.strategy_code)
            current_value = float(ticket_info.get('last'))

            data = {
                'ts': ts,
                'current_value': current_value,
                'all': acc_res.get('totalEq'),
                'ordType': strategy_config.get('ordType'),
                'attachAlgoOrds': []
            }

            if (pre_fastPeriod < pre_slowPeriod) and (fastPeriod > slowPeriod):
                if acc_res.get('pos') == '0':
                    logger.info('无仓位下多单')
                    if round_int == 0:
                        num = int(acc_res.get('availBal') * positionRatio * level / current_value)
                    else:
                        num_float = acc_res.get('availBal') * positionRatio * level / current_value
                        num = round(num_float, round_int)
                data['side'] = 'buy'
                data['posSide'] = 'long'
                data['num'] = num
                slTriggerPx = current_value*(1-stopLossRatio)
                data['attachAlgoOrds'] = [{'slTriggerPx': slTriggerPx, 'slOrdPx': '-1', 'slTriggerPxType': 'last'}]
                # 下单
                tf().order(data, self.strategy_code)
                self.STATE_IDLE = 'long'

            # 下单的时候直接把止损下进去保证及时，如果高频的话也可以用if判断比例止损，方便记录每次操作
            elif (pre_exitFastPeriod > pre_exitSlowPeriod) and (exitFastPeriod < exitSlowPeriod):
                if acc_res.get('pos') != '0':
                    # 有持仓平掉
                    logger.info('有持仓平仓')
                    num = acc_res.get('pos')
                    data['num'] = num
                    data['side'] = 'sell'
                    data['posSide'] = 'long'
                    tf().order(data, self.strategy_code)
            else:
                # 后续考虑是否记录本次策略无操作
                logger.info('本次轮训无操作')
                num = 0
                data['num'] = num
                data['side'] = 'not'
                data['posSide'] = 'long'
                tf().order(data, self.strategy_code)
        except Exception as e:
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    moving().strategy()




