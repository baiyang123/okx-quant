import os
import pathlib

import pandas as pd

from config import dev_ak, dev_sk, dev_pw, prd_ak, prd_sk, prd_pw, STRATEGY_CONFIG, ORDER_PATH, ORDER_COLUMNS, \
    STRATEGY_CLASS_CONFIG
from okx import Trade

root_dir = pathlib.Path(__file__).resolve().parent.parent
from loguru import logger

class TradeFactory:

    def __init__(self, flag=0):
        api_key = prd_ak if flag == '0' else dev_ak
        api_secret_key = prd_sk if flag == '0' else dev_sk
        passphrase = prd_pw if flag == '0' else dev_pw
        self.TradeAPI = Trade.TradeAPI(api_key, api_secret_key, passphrase, use_server_time=False, flag=flag)

    def order(self, data={}, strategy_code='', strategy_class_name='', instId=''):

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
        if strategy_code != '':
            file_name = '{}_prd.csv'.format(strategy_code)
            strategy_config = STRATEGY_CONFIG.get(strategy_code)
            clOrdCode = strategy_code.replace('-', '').replace('_', '')
        else:
            file_name = '{}_{}_prd.csv'.format(strategy_class_name, instId)
            strategy_config = STRATEGY_CLASS_CONFIG.get(strategy_class_name).get(instId)
            clOrdCode = '{}_{}'.format(strategy_class_name, instId).replace('-', '').replace('_', '')
        file_path = ORDER_PATH.format(root_dir, file_name)
        if not os.path.exists(file_path):
            with open(file_path, "w") as file:
                df = pd.DataFrame(columns=ORDER_COLUMNS)
                df.to_csv(file_path, index=False)

        order_df = pd.read_csv(file_path)
        loc = len(order_df.index)

        # 根据data下单
        instId = strategy_config.get('instId')

        if side != 'not':
            print("{}{}".format(clOrdCode, loc))
            res = self.TradeAPI.place_order(instId=instId, tdMode="isolated", clOrdId="{}{}".format(clOrdCode, loc), side=side, ordType=ordType,
                                            sz=num, posSide=posSide, attachAlgoOrds=attachAlgoOrds)
            logger.info(res)
            if res.get('code') == '0':
                # current_value 按照最后下单价格来,目前值写了单独下单，暂用data[0]后续优化
                clOrdId = res['data'][0]['clOrdId']

        # loc是整数位置，iloc是值
        data_loc = [ts, clOrdId, side, posSide, current_value, num, all]
        order_df.loc[loc] = data_loc
        order_df.to_csv(file_path, index=False)
        return res

        # todo 发邮箱等提醒



if __name__ == '__main__':
    attachAlgoOrds = [{'slTriggerPx': '0.00020524', 'slTriggerPxType': 'last', 'slOrdPx': '-1'}]
    data = {'ts': '2024-12-13', 'current_value': '0.00021524', 'all': 2.4597146257247093, 'ordType': 'market', 'num': 3, 'side': 'buy', 'posSide': 'long', 'attachAlgoOrds': attachAlgoOrds}
    print(TradeFactory().order(data, 'X-USDT-SWAP_MA'))