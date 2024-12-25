ENV = 'PRD'
TASK_SWITCH = True
'''
apikey = "75c081f0-a5ef-4154-9b88-bf45fb505772"
secretkey = "F4812F66DDDA28664CC8DF2CDDAF5F83"
IP = "10.18.19.28"
备注名 = "模拟1"
权限 = "读取/提现/交易"
'''
dev_ak = '75c081f0-a5ef-4154-9b88-bf45fb505772'
dev_sk = 'F4812F66DDDA28664CC8DF2CDDAF5F83'
dev_pw = 'Baiyang18!!'
prd_ak = 'd759cf97-a1b3-40da-9c49-911629d7b3b6'
prd_sk = 'C8C89E3E0D6FA34530F1BBD2C33DFDBF'
prd_pw = ''
'''
# instId, before, after, bar, money, lever, class_name = 'ETC-USDT-SWAP', '2023-03-05', '2024-11-05', '1D', 50000, 3, moving()
# self.FastPeriod = 5  # 入市快线周期
# self.SlowPeriod = 20  # 入市慢线周期
# # self.EnterPeriod = 2  # 入市观察期
# self.ExitFastPeriod = 5  # 离市快线周期
# self.ExitSlowPeriod = 20  # 离市慢线周期
# # self.ExitPeriod = True  # 离市观察期
# 0 生产 1模拟
'''
STRATEGY_CONFIG = {
    'BTC-USDT-SWAP_MA': {
        'instId': 'BTC-USDT-SWAP',
        'bar': '1Dutc',
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
        'ordType': 'market',
        'flag': '0'
    },
    'X-USDT-SWAP_MA': {
        'instId': 'X-USDT-SWAP',
        'bar': '1Dutc',
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
        'ordType': 'market',
        'flag': '0'
    },
    'BTC-USDT-SWAP_GRID_INF': {
        'instId': 'BTC-USDT-SWAP',
        'bar': '1Dutc',
        'boll_bar': 20,
        'atr_bar': 14,
        'ccy': 'USDT',
        'positionRatio': 0.8,
        'level': 3,
        'instType': 'SWAP',
        'stopLossRatio': 0.15,
        'interval': 10,
        'ordType': 'market',
        'flag': '1'
    },
}
COLUMNS = ['ts', 'o', 'h', 'l', 'c', 'vol', 'volCcy', 'volCcyQuote', 'confirm']
ORDER_COLUMNS = ['ts', 'clOrdId', 'operate', 'posSide', 'value', 'num', 'all']
ORDER_PATH = '{}/history_data/{}'
