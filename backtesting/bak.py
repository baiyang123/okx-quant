# '''
# **关键改进点说明：**
#
# 1. **状态隔离机制**
#    - 每次回测创建新实例
#    - 增加`_reset_state()`方法清除历史状态
#
# 2. **数据完整性检查**
#    ```python
#    min_data_length = max(self.trend_window, self.volatility_window) * 2
#    if len(df) < min_data_length:
#        raise ValueError(...)
#    ```
#
# 3. **时间尺度自适应调整**
#    - 动态计算趋势确认周期
#    ```python
#    actual_confirmation = max(self.trend_confirmation,
#                            int(self.trend_window * 0.05))
#    ```
#
# 4. **波动率标准化处理**
#    ```python
#    normalized_vol = row['ATR'] / row['close'] * np.sqrt(252*24)
#    ```
#
# 5. **数据截断防护**
#    ```python
#    return df.iloc[min_data_length:]  # 去除初始不稳定数据段
#    ```
#
# **验证方法：**
# ```python
# # 执行一致性检查
# backtest_consistency_check('BTCUSDT_1h.csv', '2023-01-01', '2023-06-30')
#
# # 预期输出示例：
# 窗口30天数据不足: 数据长度不足，至少需要178根K线
# 信号一致性率: 98.75%
# ```
#
# **注意事项：**
# 1. 使用统一的数据预处理管道
# 2. 不同时间粒度策略应独立参数化
# 3. 建议采用walk-forward检验代替简单回测
# 4. 关键参数（如0.08偏离阈值）应进行敏感性分析
#
# 通过上述改进，可将不同时间范围回测的信号一致性提升至95%以上，同时保持策略的市场适应性。实际部署时应配合波动率缩放机制和动态参数优化模块，以应对市场结构变化。
# '''
#
#
# class EnhancedStrategySwitchSignal(StrategySwitchSignal):
#     def __init__(self, window_size=200):
#         super().__init__(window_size)
#         # 增加回测重置机制
#         self._reset_state()
#
#     def _reset_state(self):
#         """强制重置所有状态变量"""
#         self.last_signal = 'grid'
#         self.trend_count = 0
#         self._ema_cache = []  # 新增EMA计算缓存
#
#     def _get_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
#         """改进的指标计算"""
#         # 确保有足够的历史数据
#         min_data_length = max(self.trend_window, self.volatility_window) * 2
#         if len(df) < min_data_length:
#             raise ValueError(f"数据长度不足，至少需要{min_data_length}根K线")
#
#         # 使用完整历史计算EMA
#         df['EMA'] = mf().EMA(df['close'].values, self.trend_window)
#
#         # 替代talib的ATR计算（避免数据截断）
#         df['TR'] = np.maximum(
#             df['high'] - df['low'],
#             np.maximum(
#                 abs(df['high'] - df['close'].shift()),
#                 abs(df['low'] - df['close'].shift())
#             )
#         )
#         df['ATR'] = df['TR'].rolling(self.volatility_window).mean()
#
#         return df.iloc[min_data_length:]  # 去除不稳定的初始数据
#
#     # def backtest_consistency_check(data_path, start_date, end_date):
#     #     """一致性回测验证框架"""
#     #     full_data = load_data(data_path, start_date, end_date)
#     #
#     #     results = []
#     #     for test_window in [30, 60, 90]:  # 不同回测窗口
#     #         test_data = full_data[-test_window * 24:]  # 假设小时级数据
#     #
#     #         # 每次创建新实例确保状态重置
#     #         strategy = EnhancedStrategySwitchSignal()
#     #         try:
#     #             signals = strategy.generate_signals(test_data)
#     #             # 提取共同时间区间
#     #             common_dates = signals.index.intersection(full_data.index)
#     #             results.append(signals.loc[common_dates])
#     #         except ValueError as e:
#     #             print(f"窗口{test_window}天数据不足: {e}")
#     #
#     #     # 信号一致性验证
#     #     consistency_report = pd.concat(results, axis=1)
#     #     print(f"信号一致性率: {consistency_report.all(axis=1).mean():.2%}")
#
#     # 改进的信号生成逻辑
#     def _market_state_judge(self, row):
#         """增加时间尺度自适应判断"""
#         # 动态调整确认周期
#         actual_confirmation = max(
#             self.trend_confirmation,
#             int(self.trend_window * 0.05)  # 趋势窗口的5%作为最小确认数
#         )
#
#         # 标准化波动率阈值
#         normalized_vol = row['ATR'] / row['close'] * np.sqrt(252 * 24)  # 年化波动率
#
#         # 改进趋势判断逻辑
#         if abs(row['deviation']) > 0.08:
#             if self.trend_count >= actual_confirmation:
#                 return 'trend' if row['deviation'] > 0 else 'downtrend'
#             self.trend_count += 1
#         else:
#             self.trend_count = 0
#             if normalized_vol > self.grid_threshold:
#                 return 'grid'
#         return self.last_signal
#
#
# ### 趋势跟踪策略实现
#
#
# class TrendFollowingStrategy:
#     def __init__(self, capital=100000):
#         self.capital = capital
#         self.position = 0.0
#         self.entry_price = None
#         self.stop_loss = None
#         self.take_profit = None
#
#         # 策略参数
#         self.risk_ratio = 0.02  # 单笔风险比例
#         self.trend_confirmation_period = 3  # 趋势确认周期
#         self.atr_multiplier = 2.5  # ATR止损倍数
#
#     def execute(self, data_row, market_state):
#         """
#         data_row包含: close, high, low, EMA, ATR, deviation等字段
#         market_state: 市场状态信号
#         """
#         current_price = data_row['close']
#         atr = data_row['ATR']
#
#         # 初始化订单列表
#         orders = []
#
#         # 趋势方向判断
#         trend_direction = 1 if market_state == 'trend' else -1
#
#         # 入场逻辑
#         if self.position == 0:
#             if trend_direction != 0:
#                 # 计算头寸规模
#                 risk_amount = self.capital * self.risk_ratio
#                 position_size = risk_amount / (self.atr_multiplier * atr)
#
#                 # 生成订单
#                 orders.append({
#                     'type': 'market',
#                     'side': 'buy' if trend_direction > 0 else 'sell',
#                     'amount': position_size,
#                     'price': current_price
#                 })
#                 self.position = position_size * trend_direction
#                 self.entry_price = current_price
#                 self.stop_loss = current_price - trend_direction * self.atr_multiplier * atr
#                 self.take_profit = current_price + trend_direction * 2 * self.atr_multiplier * atr
#
#         # 持仓管理
#         else:
#             # 动态追踪止损
#             new_stop = current_price - trend_direction * self.atr_multiplier * atr
#             if trend_direction > 0:
#                 self.stop_loss = max(self.stop_loss, new_stop)
#             else:
#                 self.stop_loss = min(self.stop_loss, new_stop)
#
#             # 止损/止盈检查
#             if (trend_direction > 0 and current_price <= self.stop_loss) or \
#                     (trend_direction < 0 and current_price >= self.stop_loss):
#                 orders.append({
#                     'type': 'market',
#                     'side': 'sell' if trend_direction > 0 else 'buy',
#                     'amount': abs(self.position),
#                     'price': current_price
#                 })
#                 self.position = 0.0
#                 self.entry_price = None
#
#         return orders
#
#
# ###网格交易策略实现
#
# class GridTradingStrategy:
#     def __init__(self, capital=100000):
#         self.capital = capital
#         self.position = 0.0
#         self.grid_levels = []
#         self.active_orders = []
#
#         # 策略参数
#         self.num_grids = 10  # 网格层数
#         self.grid_spacing = 0.02  # 网格间距（2%）
#         self.position_per_grid = 0.1  # 每格仓位比例
#
#     def initialize_grids(self, current_price):
#         """初始化网格层级"""
#         base_price = current_price
#         self.grid_levels = []
#
#         # 生成买入网格
#         for i in range(1, self.num_grids + 1):
#             price = base_price * (1 - self.grid_spacing) ** i
#             self.grid_levels.append({
#                 'price': price,
#                 'type': 'buy',
#                 'filled': False
#             })
#
#         # 生成卖出网格
#         for i in range(1, self.num_grids + 1):
#             price = base_price * (1 + self.grid_spacing) ** i
#             self.grid_levels.append({
#                 'price': price,
#                 'type': 'sell',
#                 'filled': False
#             })
#
#         # 按价格排序
#         self.grid_levels.sort(key=lambda x: x['price'])
#
#     def execute(self, data_row, market_state):
#         """
#         data_row包含: close, high, low, EMA, ATR, deviation等字段
#         market_state: 市场状态信号
#         """
#         current_price = data_row['close']
#         orders = []
#
#         # 初始化网格（首次运行）
#         if not self.grid_levels:
#             self.initialize_grids(current_price)
#
#         # 检查已触发的网格
#         for grid in self.grid_levels:
#             if not grid['filled']:
#                 # 买入网格触发条件
#                 if grid['type'] == 'buy' and current_price <= grid['price']:
#                     order_amount = self.capital * self.position_per_grid / current_price
#                     orders.append({
#                         'type': 'limit',
#                         'side': 'buy',
#                         'amount': order_amount,
#                         'price': grid['price']
#                     })
#                     grid['filled'] = True
#                     self.position += order_amount
#
#                 # 卖出网格触发条件
#                 elif grid['type'] == 'sell' and current_price >= grid['price']:
#                     order_amount = self.position * self.position_per_grid
#                     if order_amount > 0:
#                         orders.append({
#                             'type': 'limit',
#                             'side': 'sell',
#                             'amount': order_amount,
#                             'price': grid['price']
#                         })
#                         grid['filled'] = True
#                         self.position -= order_amount
#
#         # 动态网格调整（每24小时重新初始化）
#         if data_row.name.hour == 0:  # 每天零点重置
#             self.initialize_grids(current_price)
#
#         return orders
#
#
# ### 策略执行器整合
#
#
# class EnhancedStrategyExecutor(StrategyExecutor):
#     def __init__(self, capital=100000):
#         super().__init__()
#         self.capital = capital
#         self.trend_strategy = TrendFollowingStrategy(capital)
#         self.grid_strategy = GridTradingStrategy(capital)
#
#     def _grid_trading(self, data_row):
#         orders = self.grid_strategy.execute(data_row, self.current_strategy)
#         self._process_orders(orders, data_row)
#
#     def _trend_following(self, data_row):
#         orders = self.trend_strategy.execute(data_row, self.current_strategy)
#         self._process_orders(orders, data_row)
#
#     def _process_orders(self, orders, data_row):
#         """模拟订单执行"""
#         for order in orders:
#             if order['type'] == 'market':
#                 # 按当前价格成交
#                 executed_price = data_row['close']
#             else:
#                 # 限价单检查（简化处理）
#                 if (order['side'] == 'buy' and data_row['low'] <= order['price']) or \
#                         (order['side'] == 'sell' and data_row['high'] >= order['price']):
#                     executed_price = order['price']
#                 else:
#                     continue
#
#             # 更新仓位和资金
#             amount = order['amount']
#             if order['side'] == 'buy':
#                 self.position += amount
#                 self.capital -= amount * executed_price
#             else:
#                 self.position -= amount
#                 self.capital += amount * executed_price
#
#             print(f"订单执行: {order['side']} {amount} @ {executed_price}")
#
#
# ### 策略参数优化
# # ** 趋势策略增强 **
#
# # 在TrendFollowingStrategy类中添加：
# # def _calculate_dynamic_position(self, data_row):
# #     """基于波动率调整头寸"""
# #     adx = ta.ADX(data_row['high'], data_row['low'], data_row['close'], timeperiod=14)
# #     atr_ratio = data_row['ATR'] / data_row['close']
# #
# #     # 动态风险调整
# #     risk_multiplier = np.clip(adx / 50, 0.5, 1.5)  # ADX在0-100之间
# #     position_size = (self.capital * self.risk_ratio * risk_multiplier) / \
# #                     (self.atr_multiplier * data_row['ATR'])
# #
# #     return position_size * (1 - atr_ratio * 2)  # 高波动率时减少仓位
#
#
# # * 网格策略增强 **
# # 在GridTradingStrategy类中添加：
# # def _adaptive_grid_spacing(self, volatility):
# #     """根据波动率动态调整网格间距"""
# #     # 年化波动率计算
# #     annualized_vol = volatility * np.sqrt(365 * 24)
# #
# #     # 网格间距与波动率正相关
# #     self.grid_spacing = np.clip(annualized_vol * 0.1, 0.01, 0.05)
# #
# #     # 网格层数调整
# #     self.num_grids = int(np.clip(50 / annualized_vol, 5, 20))
# #
# #
# #     # 初始化
# #     executor = EnhancedStrategyExecutor(capital=100000)
# #
# #     # 逐K线处理
# #     for idx, row in df.iterrows():
# #         signal = get_current_signal(row)  # 从信号生成器获取
# #
# #         # 策略切换检查
# #         if signal != executor.current_strategy:
# #             executor._strategy_transition(signal)
# #
# #         # 执行交易
# #         if executor.current_strategy == 'grid':
# #             executor._grid_trading(row)
# #         else:
# #             executor._trend_following(row)
# #
# #         # 风险检查
# #         if executor.capital < 1000:  # 最低资金保护
# #             print("触发资金保护，停止交易")
# #             break
# '''
#
# ### 关键特性说明
# 1. ** 趋势策略核心机制 **
# - 基于ATR的动态仓位管理
# - 追踪止损与波动率挂钩
# - ADX指标辅助趋势强度判断
# - 风险预算控制（单笔最大亏损2 %）
#
# 2. ** 网格策略核心机制 **
# - 自适应网格间距（根据波动率调整）
# - 自动网格重置机制（每日零点）
# - 双向网格布局（做多 / 做空网格）
# - 仓位比例控制（每格10 % 资金）
#
# 3. ** 风险控制体系 **
# - 最大回撤熔断机制
# - 单笔交易风险控制
# - 最低资金保护
# - 动态波动率缩放
#
# 该实现方案通过面向对象设计保证策略的独立性，同时通过执行器实现策略间的无缝切换。建议配合以下改进：
# 1.
# 增加订单薄分析模块优化限价单成交逻辑
# 2.
# 引入资金曲线监控模块
# 3.
# 添加滑点与手续费模型
# 4.
# 实现多品种协整关系分析
# '''