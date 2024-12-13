ENV = 'PRD'
TASK_SWITCH = True
PASSPHRASE = 'Baiyang18!'
'''
# instId, before, after, bar, money, lever, class_name = 'ETC-USDT-SWAP', '2023-03-05', '2024-11-05', '1D', 50000, 3, moving()
# self.FastPeriod = 5  # 入市快线周期
# self.SlowPeriod = 20  # 入市慢线周期
# # self.EnterPeriod = 2  # 入市观察期
# self.ExitFastPeriod = 5  # 离市快线周期
# self.ExitSlowPeriod = 20  # 离市慢线周期
# # self.ExitPeriod = True  # 离市观察期
'''
STRATEGY_CONFIG = {
    'BTC-USDT-SWAP_MA': {
        'instId': 'BTC-USDT-SWAP',
        'bar': '1D',
        'FastPeriod': 5,
        'SlowPeriod': 20,
        'EnterPeriod': 2,
        'ExitFastPeriod': 5,
        'ExitSlowPeriod': 20,
        'ExitPeriod': True,
        'ccy': 'USDT',
        'positionRatio': 0.8,
        'level': 3,
        'instType': 'SWAP',
        'stopLossRatio': 0.15,
        'interval': 10,
        'ordType': 'market'
    },
    'X-USDT-SWAP_MA': {
        'instId': 'X-USDT-SWAP',
        'bar': '1D',
        'FastPeriod': 5,
        'SlowPeriod': 20,
        'EnterPeriod': 2,
        'ExitFastPeriod': 5,
        'ExitSlowPeriod': 20,
        'ExitPeriod': True,
        'ccy': 'USDT',
        'positionRatio': 0.8,
        'level': 3,
        'instType': 'SWAP',
        'stopLossRatio': 0.15,
        'interval': 10,
        'ordType': 'market'
    }
}
COLUMNS = ['ts', 'o', 'h', 'l', 'c', 'vol', 'volCcy', 'volCcyQuote', 'confirm']
ORDER_COLUMNS = ['ts', 'clOrdId', 'operate', 'posSide', 'value', 'num', 'all']
ORDER_PATH = '{}/history_data/{}'
