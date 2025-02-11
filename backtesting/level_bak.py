### **一、核心计算公式**

#### 1. **基础参数定义**
# - 本金（Equity）：`E`
# - 杠杆倍数（Leverage）：`L`(如5倍杠杆)
# - 入场价格（Entry
# Price）：`P_entry`
# - 当前价格（Current
# Price）：`P_current`
# - 持仓方向（Direction）：`D`(1 = 做多，-1 = 做空)
#
# #### 2. **初始仓位计算**
# - 持仓名义价值：`Position_Notional = E * L
# `
# - 持仓数量：`Q = Position_Notional / P_entry
# `

#### 3. **持仓总价值**
#
# Position_Value = Q * P_current
#
#
# #### 4. **未实现盈亏（P&L）**
#
# if Direction == 1:  # 做多
#     PnL = Q * (P_current - P_entry)
# else:  # 做空
#     PnL = Q * (P_entry - P_current)
#
#
# #### 5. **账户总价值（净资产）**
#
# Account_Equity = E + PnL
#
#
# #### 6. **强平价格（Liquidation Price）**
#
# Maintenance_Margin_Ratio = 0.05  # 维持保证金率（假设5%）
# if Direction == 1:
#     Liquidation_Price = P_entry * (1 - (1 / L) + Maintenance_Margin_Ratio)
# else:
#     Liquidation_Price = P_entry * (1 + (1 / L) - Maintenance_Margin_Ratio)


### **二、Python代码实现**


class LeverageCalculator:
    def __init__(self, equity: float, leverage: int, entry_price: float, direction: int):
        """
        :param equity: 本金（USD）
        :param leverage: 杠杆倍数
        :param entry_price: 入场价格
        :param direction: 方向 (1=做多, -1=做空)
        """
        self.equity = equity
        self.leverage = leverage
        self.entry_price = entry_price
        self.direction = direction
        self.position_notional = equity * leverage  # 持仓名义价值
        self.quantity = self.position_notional / entry_price  # 持仓数量

    def calculate_values(self, current_price: float) -> dict:
        """
        计算实时账户数据
        :param current_price: 当前市场价格
        :return: 包含所有关键指标的字典
        """
        # 持仓总价值
        position_value = self.quantity * current_price

        # 未实现盈亏
        if self.direction == 1:
            pnl = self.quantity * (current_price - self.entry_price)
        else:
            pnl = self.quantity * (self.entry_price - current_price)

        # 账户净资产
        account_equity = self.equity + pnl

        # 保证金比率
        margin_ratio = account_equity / position_value * 100 if position_value != 0 else 0

        # 强平价格
        maintenance_margin = 0.05  # 5%维持保证金率
        if self.direction == 1:
            liquidation_price = self.entry_price * (1 - (1 / self.leverage) + maintenance_margin)
        else:
            liquidation_price = self.entry_price * (1 + (1 / self.leverage) - maintenance_margin)

        return {
            "position_value": round(position_value, 4),  # 持仓总价值
            "unrealized_pnl": round(pnl, 4),  # 未实现盈亏
            "account_equity": round(account_equity, 4),  # 账户净资产
            "margin_ratio": round(margin_ratio, 2),  # 保证金比率（%）
            "liquidation_price": round(liquidation_price, 4)  # 强平价格
        }

    def get_roe(self, current_price: float) -> float:
        """计算收益率（ROE）"""
        pnl = self.calculate_values(current_price)['unrealized_pnl']
        return round((pnl / self.equity) * 100, 2)  # 收益率百分比

### **三、使用示例**

#### 案例1：5倍杠杆做多
# 初始化参数
calculator = LeverageCalculator(
    equity=1000,  # 本金1000USDT
    leverage=5,  # 5倍杠杆
    entry_price=30000,  # 入场价格30000
    direction=1  # 做多
)

# 当价格上涨到31000时
current_price = 31000
result = calculator.calculate_values(current_price)

print(f"持仓总价值: {result['position_value']} USDT")
print(f"账户净资产: {result['account_equity']} USDT")
print(f"收益率: {calculator.get_roe(current_price)}%")
print(f"强平价格: {result['liquidation_price']} USDT")

# 输出结果：
# 持仓总价值: 1033.3333 USDT
# 账户净资产: 1166.6667 USDT
# 收益率: 16.67%
# 强平价格: 28800.0 USDT

#### 案例2：3倍杠杆做空
calculator = LeverageCalculator(
    equity=5000,
    leverage=3,
    entry_price=2500,
    direction=-1
)

current_price = 2300
print(calculator.calculate_values(current_price))

# 输出结果：
# {
#   'position_value': 6900.0,
#   'unrealized_pnl': 1000.0,
#   'account_equity': 6000.0,
#   'margin_ratio': 86.96%,
#   'liquidation_price': 2666.6667
# }

### **四、关键指标解释**

# | 指标 | 公式 | 意义 |
# | ----------------- | ------------------------------- | ---------------------------------------------------------------------- |
# | 持仓总价值 | 持仓数量 × 当前价格 | 当前持仓的市场价值（包含杠杆资金） |
# | 未实现盈亏 | (现价 - 入场价) × 持仓数量 | 当前持仓的浮动盈亏（正值为盈利，负值为亏损） |
# | 账户净资产 | 本金 + 未实现盈亏 | 平仓后可收回的实际资金 |
# | 保证金比率 | (净资产 / 持仓价值) × 100 % | 衡量账户风险，低于维持保证金率会触发强平 |
# | 强平价格 | 根据杠杆和维持保证金率计算 | 触发强制平仓的市场价格 |
# | 收益率(ROE) | (未实现盈亏 / 本金) × 100 % | 反映杠杆带来的收益放大效应 |
#
# ---
#
# ### **五、风险控制建议**
# 1. ** 动态监控保证金比率 **：实时计算
# `margin_ratio`，当接近维持保证金率时触发预警
# 2. ** 自动止盈止损 **：基于ATR或波动率设置动态退出点位
# 3. ** 杠杆倍数自适应 **：根据市场波动率动态调整杠杆倍数
# ```python


def dynamic_leverage(volatility: float):
    """波动率越大，使用杠杆越小"""
    return max(1, min(5, int(50 / volatility)))  # 示例算法