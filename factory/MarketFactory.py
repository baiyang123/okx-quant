from flask import current_app

from okx import MarketData
import time
from datetime import datetime, timedelta
import pandas as pd
from config import PASSPHRASE


class MarketFactory:

    def __init__(self):
        api_key = 'd759cf97-a1b3-40da-9c49-911629d7b3b6'
        api_secret_key = 'C8C89E3E0D6FA34530F1BBD2C33DFDBF'
        passphrase = PASSPHRASE
        self.instId = 'BTC-USDT-SWAP'
        self.days = 30
        self.bar = '1D'
        self.MarketApi = MarketData.MarketAPI(api_key, api_secret_key, passphrase, use_server_time=False, flag='0')
        self.columns = ['ts', 'o', 'h', 'l', 'c', 'vol', 'volCcy', 'volCcyQuote', 'confirm']
        '''
        ts	String	开始时间，Unix时间戳的毫秒数格式，如 1597026383085
        o	String	开盘价格
        h	String	最高价格
        l	String	最低价格
        c	String	收盘价格
        vol	String	交易量，以张为单位
        如果是衍生品合约，数值为合约的张数。
        如果是币币/币币杠杆，数值为交易货币的数量。
        volCcy	String	交易量，以币为单位
        如果是衍生品合约，数值为交易货币的数量。
        如果是币币/币币杠杆，数值为计价货币的数量。
        volCcyQuote	String	交易量，以计价货币为单位
        如 BTC-USDT和BTC-USDT-SWAP，单位均是USDT。
        BTC-USD-SWAP单位是USD。
        confirm	String	K线状态
        0：K线未完结
        1：K线已完结
        '''

    def get_grid_box(self):
        # 获取30日的日线
        # get_candlesticks(self, instId, after='', before='', bar='', limit=''):
        # 获取30天前时间戳
        now = datetime.now()
        before = now - timedelta(days=self.days)
        timestamp_milliseconds = int(time.mktime(before.timetuple()) * 1000)

        res = self.MarketApi.get_candlesticks(instId=self.instId, before=timestamp_milliseconds, bar=self.bar)
        # 求最高最低，atr
        data = {}
        if res.get('code') == '0':
            df = pd.DataFrame(res.get('data'), columns=self.columns)
            df['h'] = df['h'].astype(float)
            df['l'] = df['l'].astype(float)
            df['sub'] = df['h'] - df['l']
            h, l, atr, grid_num = max(df['h']), min(df['l']), df['sub'].mean(), int(
                (max(df['h']) - min(df['l'])) / df['sub'].mean())
            data = {
                'h': h,
                'l': l,
                'atr': atr,
                'grid_num': grid_num,
            }
            return True, res.get('msg'), data
        else:
            return False, res.get('msg'), data


if __name__ == '__main__':
    print(MarketFactory().get_grid_box())
