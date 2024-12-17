import pathlib
from config import PASSPHRASE, STRATEGY_CONFIG
from okx import Account

root_dir = pathlib.Path(__file__).resolve().parent.parent


class AccountFactory:

    def __init__(self):
        api_key = 'd759cf97-a1b3-40da-9c49-911629d7b3b6'
        api_secret_key = 'C8C89E3E0D6FA34530F1BBD2C33DFDBF'
        passphrase = PASSPHRASE
        self.AccountApi = Account.AccountAPI(api_key, api_secret_key, passphrase, use_server_time=False, flag='0')

    # 获取余额以及仓位,可每天调用确定某个策略的收益，另写一方法计算每天的总收益
    def get_strategy_position(self, strategy_code):
        strategy_config = STRATEGY_CONFIG.get(strategy_code)
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
        if pos_res.get('code') == '0' and len(pos_res.get('data'))!=0:
            pos_inst = pos_res.get('data')[0]
            res['mgnMode'] = pos_inst.get('mgnMode'),  # 保证金模式isolated：逐仓
            res['posSide'] = pos_inst.get('posSide'),  # 持仓方向 long short
            res['pos'] = pos_inst.get('pos'),  # 持仓数量 张
            res['avgPx'] = pos_inst.get('avgPx'),  # 开仓均价
            res['lever'] = pos_inst.get('lever'),  # 杠杆倍数
            res['liqPx'] = pos_inst.get('liqPx'),  # 强平价
            res['markPx'] = pos_inst.get('markPx'),  # 最新标记价格
            res['margin'] = pos_inst.get('margin'),  # 保证金余额
            res['mgnRatio'] = pos_inst.get('mgnRatio'),  # 保证金率
            res['notionalUsd'] = pos_inst.get('mgnRatio'),  # 保证金率
            res['bePx'] = pos_inst.get('bePx'),  # 盈亏平衡价
            res['upl'] = pos_inst.get('upl'),  # 未实现收益
            res['uplRatio'] = pos_inst.get('uplRatio'),  # 未实现收益率
            res['realizedPnl'] = pos_inst.get('realizedPnl'),  # 已实现收益（手续费什么的，加上已经平了的部分收益）

        return res

    def get_lotSz(self, strategy_code):
        strategy_config = STRATEGY_CONFIG.get(strategy_code)
        instId = strategy_config.get('instId')
        swap = strategy_config.get('instType')
        res = self.AccountApi.get_instruments(instType=swap, instId=instId)
        if res.get('data')[0].get('lotSz') == '1':
            lotsz = 0
        else:
            lotsz = len((res.get('data')[0].get('lotSz')).split('.')[0])
        return lotsz


if __name__ == '__main__':
    # print(MarketFactory().get_grid_box())
    # print(MarketFactory().get_history_data('BTC-USDT-SWAP', '2023-03-05', '2024-11-05', '1D'))
    # print(AccountFactory().get_strategy_position('X-USDT-SWAP_MA'))
    print(AccountFactory().get_lotSz('BTC-USDT-SWAP_MA'))