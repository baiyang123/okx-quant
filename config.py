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
dev_pw = ''
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
# 0 生产 1模拟  时间粒度，默认值1m
# 如 [1m/3m/5m/15m/30m/1H/2H/4H]
# 香港时间开盘价k线：[6H/12H/1D/2D/3D/1W/1M/3M]
# UTC时间开盘价k线：[/6Hutc/12Hutc/1Dutc/2Dutc/3Dutc/1Wutc/1Mutc/3Mutc]
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
        'lever': 3,
        'instType': 'SWAP',
        'stopLossRatio': 0.15,
        'interval': 10,
        'ordType': 'market',
        'flag': '0',
        'str_class': 'moving',
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
        'lever': 3,
        'instType': 'SWAP',
        'stopLossRatio': 0.15,
        'interval': 10,
        'ordType': 'market',
        'flag': '0',
        'str_class': 'moving',
    },
    'BTC-USDT-SWAP_GRID_INF': {
        'instId': 'BTC-USDT-SWAP',
        'bar_unit': 'Dutc',
        'bar': 1,
        'boll_bar': 20,
        'atr_bar': 14,
        'ccy': 'USDT',
        'positionRatio': 0.8,
        'lever': 5,
        'instType': 'SWAP',
        'stopLossRatio': 0.15,
        'interval': 10,
        'ordType': 'market',
        'flag': '1',
        'initial_position': 0.2,
        'grid_position': 0.05,
        'direction': 2,  # 0做多1做空2双向
        'str_class': 'GridInf',
    },
}
COLUMNS = ['ts', 'o', 'h', 'l', 'c', 'vol', 'volCcy', 'volCcyQuote', 'confirm']
ORDER_COLUMNS = ['ts', 'clOrdId', 'operate', 'posSide', 'order_value', 'current_value', 'num', 'all']
GRID_INF_OPERATION_COLUMNS = ['instId', 'buyp', 'sellp', 'direction', 'initial_num', 'grid_num']
GRID_INF_OPERATION_COLUMNS_TESTING = ['instId', 'buyp', 'sellp', 'direction', 'initial_num', 'grid_num', 'position', 'lbpos', 'lspos', 'sspos', 'sbpos', 'all', 'all_start', 'remain']
GRID_INF_OPERATION_HISTORY_TESTING = ['ts', 'instId', 'buyp', 'sellp', 'direction', 'initial_num', 'grid_num', 'position', 'lbpos', 'lspos', 'sspos', 'sbpos', 'all', 'all_start', 'remain','current_value']
ORDER_COLUMNS_TESTING = ['ts', 'clOrdId', 'operate', 'posSide', 'order_value', 'current_value', 'num', 'all']
ORDER_PATH = '{}/history_data/{}'
STRATEGY_CLASS_CONFIG = {
    'GridInf': {
        'BTC-USDT-SWAP': {
            'instId': 'BTC-USDT-SWAP',
            'bar_unit': 'Dutc',  # 时间周期单位，香港
            'bar': 1,
            'boll_bar': 20,
            'atr_bar': 14,  # 算每天震荡均值
            'ccy': 'USDT',
            'positionRatio': 0.8,  # 策略仓位
            'lever': 5,
            'instType': 'SWAP',
            'stopLossRatio': 0.15,  # 止损比例
            'interval': 10,  # 策略运行频率
            'ordType': 'market',
            'flag': '1',  # 1模拟0实盘
            'initial_position': 0.2,  # 底仓仓位
            'grid_position': 0.05,  # 网格仓位
            'pos_direction': 2,  # 0做多1做空2双向
            'frequency': 1,  # 每天的触网频率
        }
    },
    'Grid_Testing': {
            'BTC-USDT-SWAP': {
                'instId': 'BTC-USDT-SWAP',
                'bar_unit': 'Dutc',  # 时间周期单位，香港
                'bar': 1,
                'boll_bar': 20,
                'atr_bar': 14,  # 算每天震荡均值
                'ccy': 'USDT',
                'positionRatio': 0.8,  # 策略仓位
                'lever': 1,
                'instType': 'SWAP',
                'stopLossRatio': 0.15,  # 止损比例
                'interval': 10,  # 策略运行频率
                'ordType': 'market',
                'flag': '1',  # 1模拟0实盘
                'initial_position': 0.2,  # 底仓仓位
                'grid_position': 0.05,  # 网格仓位
                'pos_direction': 2,  # 0做多1做空2双向
                'frequency': 1,  # 每天的触网频率
            }
        }
}