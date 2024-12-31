import pathlib
from config import dev_ak, dev_sk, dev_pw, prd_ak, prd_sk, prd_pw, STRATEGY_CONFIG, STRATEGY_CLASS_CONFIG
from okx import Account
from loguru import logger

root_dir = pathlib.Path(__file__).resolve().parent.parent


class AccountFactory:

    def __init__(self, flag='0'):
        api_key = prd_ak if flag == '0' else dev_ak
        api_secret_key = prd_sk if flag == '0' else dev_sk
        passphrase = prd_pw if flag == '0' else dev_pw
        self.AccountApi = Account.AccountAPI(api_key, api_secret_key, passphrase, use_server_time=False, flag=flag)

    # 获取余额以及仓位,可每天调用确定某个策略的收益，另写一方法计算每天的总收益
    def get_strategy_position(self, strategy_code='', strategy_class_name='', instId=''):
        if strategy_code != '':
            strategy_config = STRATEGY_CONFIG.get(strategy_code)
        else:
            strategy_config = STRATEGY_CLASS_CONFIG.get(strategy_class_name).get(instId)
        ccy = strategy_config.get('ccy')
        # 账户
        acc_res = self.AccountApi.get_account_balance(ccy=ccy)
        details = acc_res.get('data')[0].get('details')

        # USDT
        for detail in details:
            if detail.get('ccy') == ccy:
                availBal = detail.get('availBal')
                break

        # data虽然是个list但只会返回一个元素
        totalEq = float(acc_res.get('data')[0].get('totalEq'))
        isoEq = float(acc_res.get('data')[0].get('isoEq'))

        # 目前这里只出了部分有用的字段 https://www.okx.com/docs-v5/zh/#trading-account-rest-api-get-positions
        '''
        realizedPnl	String	已实现收益
        仅适用于交割/永续/期权
        realizedPnl=pnl+fee+fundingFee+liqPenalty
        pnl	String	平仓订单累计收益额
        fee	String	累计手续费金额，正数代表平台返佣 ，负数代表平台扣除
        fundingFee	String	累计资金费用
        liqPenalty	String	累计爆仓罚金，有值时为负数。
        '''
        res = {
            'totalEq': totalEq,  # 美金层面权益 账户总金额
            'isoEq': isoEq,  # 币种逐仓仓位权益 仓位总金额
            'availBal': float(availBal),  # 可用余额
        }

        instId = strategy_config.get('instId')
        # 仓位
        pos_res = self.AccountApi.get_positions(instId=instId)
        # todo 这里以后如果支持一个策略扫多个品种会变成循环放list
        if pos_res.get('code') == '0' and len(pos_res.get('data')) != 0:
            res['pos_res'] = pos_res['data']
        else:
            res['pos_res'] = []
            # pos_inst = pos_res.get('data')[0]
            # res['mgnMode'] = pos_inst.get('mgnMode'),  # 保证金模式isolated：逐仓
            # res['posSide'] = pos_inst.get('posSide'),  # 持仓方向 long short
            # res['pos'] = pos_inst.get('pos'),  # 持仓数量 张
            # res['avgPx'] = pos_inst.get('avgPx'),  # 开仓均价
            # res['lever'] = pos_inst.get('lever'),  # 杠杆倍数
            # res['liqPx'] = pos_inst.get('liqPx'),  # 强平价
            # res['markPx'] = pos_inst.get('markPx'),  # 最新标记价格
            # res['margin'] = pos_inst.get('margin'),  # 保证金余额
            # res['mgnRatio'] = pos_inst.get('mgnRatio'),  # 保证金率
            # res['notionalUsd'] = pos_inst.get('mgnRatio'),  # 保证金率
            # res['bePx'] = pos_inst.get('bePx'),  # 盈亏平衡价
            # res['upl'] = pos_inst.get('upl'),  # 未实现收益
            # res['uplRatio'] = pos_inst.get('uplRatio'),  # 未实现收益率
            # res['realizedPnl'] = pos_inst.get('realizedPnl'),  # 已实现收益（手续费什么的，加上已经平了的部分收益）

        return res

    def get_lotSz(self, strategy_code='', strategy_class_name='', instId=''):
        if strategy_code != '':
            strategy_config = STRATEGY_CONFIG.get(strategy_code)
        else:
            strategy_config = STRATEGY_CLASS_CONFIG.get(strategy_class_name).get(instId)
        instId = strategy_config.get('instId')
        swap = strategy_config.get('instType')
        flag = strategy_config.get('flag')
        res = AccountFactory(flag).AccountApi.get_instruments(instType=swap, instId=instId)
        if res.get('data')[0].get('lotSz') == '1':
            lotsz = 0
        else:
            lotsz = len((res.get('data')[0].get('lotSz')).split('.')[0])
        return lotsz

    def set_levelage(self, strategy_code='', strategy_class_name='', instId=''):
        if strategy_code != '':
            strategy_config = STRATEGY_CONFIG.get(strategy_code)
        else:
            strategy_config = STRATEGY_CLASS_CONFIG.get(strategy_class_name).get(instId)
        instId = strategy_config.get('instId')
        lever = strategy_config.get('lever')
        flag = strategy_config.get('flag')
        long_res = AccountFactory(flag).AccountApi.set_leverage(instId=instId, lever=lever, mgnMode='isolated',
                                                           posSide='long')
        short_res = AccountFactory(flag).AccountApi.set_leverage(instId=instId, lever=lever, mgnMode='isolated',
                                                           posSide='short')
        if long_res.get('code') != '0' or short_res.get('code') != '0':
            logger.error('设置杠杆失败{}-{}'.format(long_res, short_res))
            raise Exception('设置杠杆失败{}-{}'.format(long_res, short_res))


if __name__ == '__main__':
    # print(MarketFactory().get_grid_box())
    # print(MarketFactory().get_history_data('BTC-USDT-SWAP', '2023-03-05', '2024-11-05', '1D'))
    # print(AccountFactory('1').get_strategy_position(strategy_class_name='GridInf', instId='BTC-USDT-SWAP'))
    # print(AccountFactory().get_lotSz('BTC-USDT-SWAP_MA'))
    print(AccountFactory('1').set_levelage(strategy_class_name='GridInf', instId='BTC-USDT-SWAP'))