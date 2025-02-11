import datetime
import pathlib
import time

import pandas as pd
import numpy as np
# import talib as ta
from typing import Tuple
import matplotlib.pyplot as plt

from factory.MarketFactory import MarketFactory

root_dir = pathlib.Path(__file__).resolve().parent.parent

'''
代码核心功能说明：

1. 指标计算层：
- 使用EMA(89)作为趋势判断基准线
- 结合ATR(20)衡量市场波动率
- RSI(14)识别超买超卖状态
- 价格偏离度指标量化趋势强度

2. 信号生成逻辑：
- 当价格偏离EMA超过8%且RSI未达极端值时触发趋势信号
- 波动率高于阈值且偏离度适中时维持网格策略
- 需要连续3根K线确认趋势形成

3. 策略切换机制：
- 趋势策略启动时保留80%网格仓位
- 切回网格时减仓50%控制风险
- 实时仓位状态跟踪

4. 可视化模块：
- 展示价格走势与信号触发位置
- 显示策略运行状态变化
- 支持多时间框架分析

改进建议：
1. 增加高频数据处理模块（websocket实时数据接入）
2. 集成风险控制模块（动态止盈止损）
3. 添加回测统计指标（夏普比率、最大回撤等）
4. 优化参数自适应机制（使用遗传算法优化阈值参数）

该框架需要配合具体的网格和趋势策略实现细节，可根据实际交易需求扩展仓位管理模块和订单执行接口。
'''


class StrategySwitchSignal:
    def __init__(self, window_size=200):
        # 参数初始化
        self.trend_window = 89  # 趋势判断EMA周期
        self.volatility_window = 20  # 波动率计算周期
        self.rsi_window = 14  # RSI超买超卖周期
        self.grid_threshold = 0.15  # 网格触发波动阈值
        self.trend_confirmation = 3  # 趋势确认所需连续K线数

        # 状态缓存
        self.last_signal = 'grid'
        self.trend_count = 0

    def _get_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        mf = MarketFactory()
        df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('Date', inplace=True)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        mf.EMA(df, timeperiod=self.trend_window)
        mf.ATR(df, self.volatility_window)
        mf.RSI(df, self.rsi_window)

        # 计算价格与EMA偏离度
        df['deviation'] = (df['close'] - df['EMA']) / df['EMA']
        return df.dropna()

    def _market_state_judge(self, row) -> str:
        """判断市场状态"""
        # 波动率条件
        volatility_cond = row['ATR'] / row['close'] > self.grid_threshold

        # 趋势方向条件
        trend_strength = abs(row['deviation'])  # 偏离度
        trend_direction = np.sign(row['deviation'])

        # RSI边界条件
        rsi_cond = (row['RSI'] > 70) | (row['RSI'] < 30)

        # 综合判断逻辑
        # if trend_strength > 0.08 and not rsi_cond:
        if trend_strength > 0.08:
            if self.trend_count >= self.trend_confirmation:
                return 'trend' if trend_direction > 0 else 'downtrend'
            self.trend_count += 1
        else:
            self.trend_count = 0
            if volatility_cond and 0.03 < trend_strength < 0.08:
                return 'grid'
        # return self.last_signal  # 默认维持上次状态
        return self.last_signal

    def generate_signals(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        """生成切换信号"""
        df = self._get_indicators(ohlcv.copy())
        signals = []
        # print(df)
        df.sort_index().to_csv('{}/operation_data/indicators.csv'.format(root_dir), index=True)

        for idx, row in df.iterrows():
            current_signal = self._market_state_judge(row)
            signals.append({
                'timestamp': idx,
                'market_state': current_signal,
                'deviation': row['deviation'],  # 偏离度
                'volatility': row['ATR'] / row['close']  # 波动率
            })
            self.last_signal = current_signal

        return pd.DataFrame(signals).set_index('timestamp')


class StrategyExecutor:
    def __init__(self):
        self.current_strategy = 'grid'
        self.position = 0.0

    def execute_strategy(self, signal_df: pd.DataFrame):
        """策略执行模拟"""
        results = []

        for idx, row in signal_df.iterrows():
            # 策略切换逻辑
            if row['market_state'] != self.current_strategy:
                self._strategy_transition(row['market_state'])

            # 模拟策略执行（需根据具体策略实现）
            if self.current_strategy == 'grid':
                self._grid_trading(idx, row)
            else:
                self._trend_following(idx, row)

            results.append({
                'timestamp': idx,
                'strategy': self.current_strategy,
                'position': self.position
            })

        return pd.DataFrame(results).set_index('timestamp')

    def _strategy_transition(self, new_strategy: str):
        """策略切换时的仓位调整"""
        print(f"Strategy switching from {self.current_strategy} to {new_strategy}")

        # 清仓过渡逻辑（示例）
        if self.current_strategy == 'grid' and new_strategy == 'trend':
            self.position *= 0.8  # 保留80%仓位转向趋势
        elif self.current_strategy == 'trend' and new_strategy == 'grid':
            self.position *= 0.5  # 减半仓位转向网格
        self.current_strategy = new_strategy

    def _grid_trading(self, idx, data_row):
        """网格策略逻辑"""
        # 实现具体的网格交易逻辑
        print(idx, data_row)

        pass

    def _trend_following(self, idx, data_row):
        """趋势跟踪策略"""
        # 实现具体的趋势跟踪逻辑
        print(idx, data_row)
        pass


if __name__ == "__main__":
    # 获取历史数据（示例）
    # now = datetime.datetime.now()
    # before = now - datetime.timedelta(days=100)
    # # 循环查出所有时间
    # timestamp_milliseconds = int(time.mktime(before.timetuple()) * 1000)
    mf = MarketFactory()
    before = '2024-01-01'
    after = '2025-02-10'
    df = mf.get_history_candles_data(instId='BTC-USDT-SWAP', before=before, after=after, bar='1Dutc')
    # df = pd.DataFrame(res.get('data'), columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy',
    #                                    'volCcyQuote', 'confirm'])
    df['close'] = df['close'].astype(float)
    df.set_index(pd.to_datetime(df['timestamp'], unit='ms'), inplace=True)
    df.sort_index().to_csv('{}/operation_data/df.csv'.format(root_dir), index=True)

    # 生成信号
    signal_generator = StrategySwitchSignal()
    signals = signal_generator.generate_signals(df)

    signals.sort_index().to_csv('{}/operation_data/singnals.csv'.format(root_dir), index=True)

    # 执行策略切换
    executor = StrategyExecutor()
    result = executor.execute_strategy(signals)

    result.sort_index().to_csv('{}/operation_data/convert.csv'.format(root_dir), index=True)

    # 可视化结果

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    df['close'].plot(ax=ax1, title='Price')

    # df_chuli = pd.read_csv('{}/operation_data/indicators.csv'.format(root_dir))
    # df_chuli['EMA'].plot(ax=ax1, title='EMA')

    signals['market_state'].apply(lambda x: 1 if x == 'trend' else 0).plot(ax=ax1, secondary_y=True, style='g--')

    result['strategy'].apply(lambda x: 1 if x == 'trend' else 0).plot(ax=ax2, title='Strategy Status')

    # di = {"trend": 1, "downtrend": -1, "grid": 0}

    # signals['market_state'].apply(lambda x: di[x]).plot(ax=ax1, secondary_y=True, style='g--')
    #
    # result['strategy'].apply(lambda x: di[x]).plot(ax=ax2, title='Strategy Status')
    plt.show()
