import pathlib
import time
from datetime import datetime, timedelta
import pandas as pd
from config import PASSPHRASE, STRATEGY_CONFIG, COLUMNS
from okx import MarketData

root_dir = pathlib.Path(__file__).resolve().parent.parent

'''
开始结束时间，币种，周期，初始资金，杠杆（默认1），网格：初始仓位，单网成交，网格距离，开仓点位，高低网边缘
---------------实盘疑虑使用get_fast_low_ma模式，入参策略code其他从配置文件获取---------------------------------
'''


class MarketFactory:

    def __init__(self, flag=0):
        api_key = 'd759cf97-a1b3-40da-9c49-911629d7b3b6'
        api_secret_key = 'C8C89E3E0D6FA34530F1BBD2C33DFDBF'
        passphrase = PASSPHRASE
        self.MarketApi = MarketData.MarketAPI(api_key, api_secret_key, passphrase, use_server_time=False, flag=flag)
        # self.columns = ['ts', 'o', 'h', 'l', 'c', 'vol', 'volCcy', 'volCcyQuote', 'confirm']
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

    def get_grid_box(self, instId, bar, days):
        # 获取30日的日线
        # get_candlesticks(self, instId, after='', before='', bar='', limit=''):
        # 获取30天前时间戳
        now = datetime.now()
        before = now - timedelta(days=days)
        timestamp_milliseconds = int(time.mktime(before.timetuple()) * 1000)

        res = self.MarketApi.get_candlesticks(instId=instId, before=timestamp_milliseconds, bar=bar)
        # 求最高最低，atr
        data = {}
        if res.get('code') == '0':
            df = pd.DataFrame(res.get('data'), columns=COLUMNS)
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
        history_data_list = []
        data_res = True
        date_format = "%Y-%m-%d"
        before_datetime = datetime.strptime(before, date_format)
        after_datetime = datetime.strptime(after, date_format)

        delta = after_datetime - before_datetime

        time_bar = bar[1]
        if time_bar == 'D':
            delta = delta.days

        # okx最多返回1440条数据，每次返回300分页
        if delta > 1440:
            raise Exception('周期差不能超过1440')
        else:
            while before_datetime < after_datetime:
                before_timestamp = int(time.mktime(before_datetime.timetuple()) * 1000)
                after_datetime_n = before_datetime - timedelta(days=-300) if before_datetime - timedelta(
                    days=-300) < after_datetime else after_datetime
                after_timestamp = int(time.mktime(after_datetime_n.timetuple()) * 1000)
                # 超过300天分批查到1440天,拼接结果
                res = self.MarketApi.get_candlesticks(instId=instId, before=before_timestamp, after=after_timestamp,
                                                      bar=bar, limit=1000)
                if res.get('code') == '0':
                    # history_data_list = history_data_list + res.get('data')
                    history_data_list.extend(res.get('data'))
                    before_datetime = before_datetime - timedelta(days=-209)
                else:
                    data_res = False
                    break
            if data_res:
                df = pd.DataFrame(history_data_list, columns=self.columns)
                df['h'] = df['h'].astype(float)
                df['l'] = df['l'].astype(float)
                df['c'] = df['c'].astype(float)
                df['ts'] = df['ts'].astype(str)
                # 只取日期中的某些信息：dt.XXXX (XXXX= date、time、hour、year、month、day)
                df['ts'] = pd.to_datetime(df['ts'], unit='ms').dt.date
                income = df['c'].iloc[0] - df['c'].iloc[-1]
                percentage = round(income / df['c'].iloc[-1] * 100, 2)
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
        return True, res.get('msg'), income, str(percentage) + '%'

    def get_fast_low_ma(self, strategy_code):
        strategy_config = STRATEGY_CONFIG.get(strategy_code)
        bar = strategy_config.get('bar')
        instId = strategy_config.get('instId')
        SlowPeriod = strategy_config.get('SlowPeriod')
        FastPeriod = strategy_config.get('FastPeriod')
        ExitSlowPeriod = strategy_config.get('ExitSlowPeriod')
        ExitFastPeriod = strategy_config.get('ExitFastPeriod')
        timedelta_bar = max(SlowPeriod, ExitSlowPeriod)

        after_datetime = datetime.now()
        after_timestamp = int(time.mktime(after_datetime.timetuple()) * 1000)
        # 多出两天计算快慢均线
        before_datetime = after_datetime - timedelta(days=timedelta_bar + 2)
        before_timestamp = int(time.mktime(before_datetime.timetuple()) * 1000)

        res = self.MarketApi.get_candlesticks(instId=instId, before=before_timestamp, after=after_timestamp,
                                              bar=bar,
                                              limit=1000)
        if res.get('code') == '0':
            df = pd.DataFrame(res.get('data'), columns=COLUMNS)
        else:
            raise Exception(res.get('msg'))

        # 通过df计算快当天慢线 当前价格
        df['h'] = df['h'].astype(float)
        df['l'] = df['l'].astype(float)
        df['c'] = df['c'].astype(float)
        df['ts'] = df['ts'].astype(str)
        # 只取日期中的某些信息：dt.XXXX (XXXX= date、time、hour、year、month、day)
        df['ts'] = pd.to_datetime(df['ts'], unit='ms').dt.date

        df_sorted_by_column = df.sort_values(by='ts', ascending=True)
        df_sorted_by_column['ma_fp_{}'.format(FastPeriod)] = round(df_sorted_by_column['c'].rolling(FastPeriod).mean(),
                                                                   2)
        df_sorted_by_column['ma_sp_{}'.format(SlowPeriod)] = round(df_sorted_by_column['c'].rolling(SlowPeriod).mean(),
                                                                   2)
        df_sorted_by_column['ma_efp_{}'.format(ExitFastPeriod)] = round(df_sorted_by_column['c'].rolling(ExitFastPeriod)
                                                                        .mean(), 2)
        df_sorted_by_column['ma_esp_{}'.format(ExitSlowPeriod)] = round(df_sorted_by_column['c'].rolling(ExitSlowPeriod)
                                                                        .mean(), 2)
        # 设置均线
        filled_df = df_sorted_by_column.copy().fillna(0)
        # iloc为行列证书索引，loc为行列名索引
        data = filled_df.iloc[-1]
        pre_data = filled_df.iloc[-2]

        fl_res = {
            'pre_fp': pre_data['ma_fp_{}'.format(FastPeriod)],
            'pre_sp': pre_data['ma_sp_{}'.format(SlowPeriod)],
            'pre_efp': pre_data['ma_efp_{}'.format(ExitFastPeriod)],
            'pre_esp': pre_data['ma_esp_{}'.format(ExitSlowPeriod)],
            'fp': data['ma_fp_{}'.format(FastPeriod)],
            'sp': data['ma_sp_{}'.format(SlowPeriod)],
            'efp': data['ma_efp_{}'.format(ExitFastPeriod)],
            'esp': data['ma_esp_{}'.format(ExitSlowPeriod)],
            'c': data['c']
        }

        return fl_res

    def get_ticker_info(self, strategy_code):
        strategy_config = STRATEGY_CONFIG.get(strategy_code)
        instId = strategy_config.get('instId')
        res = self.MarketApi.get_ticker(instId)
        if res.get('code') == '0':
            return res.get('data')[0]
        else:
            raise Exception(res.get('msg'))

if __name__ == '__main__':
    # print(MarketFactory().get_grid_box())
    # print(MarketFactory().get_history_data('BTC-USDT-SWAP', '2023-03-05', '2024-11-05', '1D'))
    print(MarketFactory().get_ticker_info('BTC-USDT-SWAP_MA'))
