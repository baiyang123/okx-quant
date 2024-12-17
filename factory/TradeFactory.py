import os
import pathlib

import pandas as pd

from config import PASSPHRASE, STRATEGY_CONFIG, ORDER_PATH, ORDER_COLUMNS
from okx import Trade

root_dir = pathlib.Path(__file__).resolve().parent.parent
from loguru import logger

class TradeFactory:

    def __init__(self, flag=0):
        api_key = 'd759cf97-a1b3-40da-9c49-911629d7b3b6'
        api_secret_key = 'C8C89E3E0D6FA34530F1BBD2C33DFDBF'
        passphrase = PASSPHRASE
        self.TradeAPI = Trade.TradeAPI(api_key, api_secret_key, passphrase, use_server_time=False, flag=flag)

    def order(self, data, strategy_code):

        logger.info(data)

        ts = data.get('ts')
        current_value = data.get('current_value')
        all = data.get('all')
        side = data.get('side')
        posSide = data.get('posSide')
        num = data.get('num')
        ordType = data.get('ordType')
        attachAlgoOrds = data.get('attachAlgoOrds')
        clOrdId = 'NOT'

        # 记录策略记录
        file_name = '{}_prd.csv'.format(strategy_code)
        file_path = ORDER_PATH.format(root_dir, file_name)
        if not os.path.exists(file_path):
            with open(file_path, "w") as file:
                df = pd.DataFrame(columns=ORDER_COLUMNS)
                df.to_csv(file_path, index=False)

        order_df = pd.read_csv(file_path)
        loc = len(order_df.index)

        # 根据data下单
        strategy_config = STRATEGY_CONFIG.get(strategy_code)
        instId = strategy_config.get('instId')
        clOrdCode = strategy_code.replace('-', '').replace('_', '')

        if side != 'not':
            res = self.TradeAPI.place_order(instId=instId, tdMode="isolated", clOrdId="{}{}".format(clOrdCode, loc), side=side, ordType=ordType,
                                            sz=num, posSide=posSide, attachAlgoOrds=attachAlgoOrds)
            logger.info(res)
            if res.get('code') == '0':
                # current_value 按照最后下单价格来,目前值写了单独下单，暂用data[0]后续优化
                clOrdId = data['0']

        # loc是整数位置，iloc是值
        data_loc = [ts, clOrdId, side, posSide, current_value, num, all]
        order_df.loc[loc] = data_loc
        order_df.to_csv(file_path, index=False)

        # todo 发邮箱等提醒



if __name__ == '__main__':
    attachAlgoOrds = [{'slTriggerPx': '0.00020524', 'slTriggerPxType': 'last', 'slOrdPx': '-1'}]
    data = {'ts': '2024-12-13', 'current_value': '0.00021524', 'all': 2.4597146257247093, 'ordType': 'market', 'num': 3, 'side': 'buy', 'posSide': 'long', 'attachAlgoOrds': attachAlgoOrds}
    print(TradeFactory().order(data, 'X-USDT-SWAP_MA'))