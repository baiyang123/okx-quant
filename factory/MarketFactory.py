from flask import current_app

from okx import MarketData
import time
from datetime import datetime, timedelta
import pandas as pd
from config import PASSPHRASE
import matplotlib.pyplot as plt

import sys
import os

import pathlib

root_dir = pathlib.Path(__file__).resolve().parent.parent

'''
开始结束时间，币种，周期，初始资金，杠杆（默认1），网格：初始仓位，单网成交，网格距离，开仓点位，高低网边缘
'''
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

    '''
    开始结束时间，币种，周期
    时间粒度，默认值1m
    如 [1s/1m/3m/5m/15m/30m/1H/2H/4H]
    香港时间开盘价k线：[6H/12H/1D/2D/3D/1W/1M/3M]
    UTC时间开盘价k线：[6Hutc/12Hutc/1Dutc/2Dutc/3Dutc/1Wutc/1Mutc/3Mutc]pyplot设置线备注
    '''
    # 历史数据查询并生成文件，便于后续回测
    def get_history_data(self, instId, before, after, bar):
        date_format = "%Y-%m-%d"
        before_datetime = datetime.strptime(before, date_format)
        after_datetime = datetime.strptime(after, date_format)
        before_timestamp = int(time.mktime(before_datetime.timetuple()) * 1000)
        after_timestamp = int(time.mktime(after_datetime.timetuple()) * 1000)
        res = self.MarketApi.get_candlesticks(instId=instId, before=before_timestamp, after=after_timestamp, bar=bar, limit=1000)
        if res.get('code') == '0':
            df = pd.DataFrame(res.get('data'), columns=self.columns)
            df['h'] = df['h'].astype(float)
            df['l'] = df['l'].astype(float)
            df['c'] = df['c'].astype(float)
            df['ts'] = df['ts'].astype(str)
            # 只取日期中的某些信息：dt.XXXX (XXXX= date、time、hour、year、month、day)
            df['ts'] = pd.to_datetime(df['ts'], unit='ms').dt.date
            income = df['c'].iloc[0]-df['c'].iloc[-1]
            percentage = round(income/df['c'].iloc[-1]*100, 2)
            df_sorted_by_column = df.sort_values(by='ts', ascending=True)
            df_sorted_by_column['ma5'] = round(df_sorted_by_column['c'].rolling(5).mean(), 2)
            df_sorted_by_column['ma20'] = round(df_sorted_by_column['c'].rolling(20).mean(), 2)
            # 设置均线
            filled_df = df_sorted_by_column.copy().fillna(0)
            filled_df.to_csv('{}/history_data/history_data_{}_{}.csv'.format(root_dir, instId, bar), index=False)
            # plt.plot(df['ts'], df['c'])
            # plt.xlabel('时间')
            # plt.ylabel('价格')
            # 设置Matplotlib的中文字体
            # plt.rcParams['font.sans-serif'] = ['SimHei']
            # plt.show()

        else:
            return False, res.get('msg'), 0, 0
        return True, res.get('msg'), income, str(percentage)+'%'


if __name__ == '__main__':
    # print(MarketFactory().get_grid_box())
    print(MarketFactory().get_history_data('BTC-USDT-SWAP', '2024-11-01', '2024-11-28', '1D'))