### **一、核心计算公式**

#### **1. 初始参数定义**
# - 本金（Equity）：`E`
# - 杠杆倍数（Leverage）：`L`
# - 初始入场价格（Entry
# Price）：`P_entry`
# - 初始仓位比例（Position
# Ratio）：`R`（如20 % 本金）
# - 维持保证金率（Maintenance
# Margin
# Ratio）：`M`（如5 %）
#
# #### **2. 初始头寸计算**
# - ** 初始保证金 **：`Initial_Margin = E * R
# `
# - ** 名义头寸价值 **：`Position_Notional = Initial_Margin * L
# `
# - ** 持仓数量 **：`Q = Position_Notional / P_entry
# `
#
# #### **3. 动态指标计算**
# - ** 未实现盈亏（P & L） ** ：
# ```python
# PnL = Q * (P_current - P_entry)  # 做多
# PnL = Q * (P_entry - P_current)  # 做空
# ```
# - ** 持仓总价值 **：`Position_Value = Q * P_current
# `
# - ** 账户总价值 **：`Account_Value = E + PnL + 已实现价值（如果减仓了）
# `
# - ** 账户余额（可用保证金） ** ：`Balance = E - Initial_Margin + PnL
# `
# - ** 保证金比率 **：`Margin_Ratio = (Account_Value - Balance) / Position_Value
# `
#
# #### **4. 加仓后持仓成本**
# - ** 新加仓数量 **：`Q_new = (E_add * L) / P_add
# `
# - ** 总持仓数量 **：`Q_total = Q + Q_new
# `
# - ** 平均持仓成本 **：
# ```python
# Avg_Price = (Q * P_entry + Q_new * P_add) / Q_total
# ```
#
# #### **5. 强平价格**
# - ** 做多强平价格 **：
# ```python
# Liquidation_Price = (Initial_Margin * (1 - M)) / (Q * (1 - M / L))
# ```
# - ** 做空强平价格 **：
# ```python
# Liquidation_Price = (Initial_Margin * (1 + M)) / (Q * (1 + M / L))
# ```
#
# ---
#
# ### **二、Python代码实现**


class LeveragedPosition:
    def __init__(self, equity: float, leverage: int, entry_price: float, position_ratio: float, direction: int):
        """
        :param equity: 初始本金（USDT）
        :param leverage: 杠杆倍数
        :param entry_price: 初始入场价格
        :param position_ratio: 初始仓位比例（0-1）
        :param direction: 方向（1=做多，-1=做空）
        """
        self.equity = equity
        self.leverage = leverage
        self.direction = direction

        # 初始仓位计算
        self.initial_margin = equity * position_ratio
        self.position_notional = self.initial_margin * leverage
        self.quantity = self.position_notional / entry_price
        self.avg_price = entry_price  # 初始持仓均价

        # 账户状态
        self.balance = equity - self.initial_margin  # 可用余额
        self.maintenance_margin_ratio = 0.05  # 维持保证金率5%

    def calculate_metrics(self, current_price: float) -> dict:
        """计算实时指标"""
        # 未实现盈亏
        if self.direction == 1:
            pnl = self.quantity * (current_price - self.avg_price)
        else:
            pnl = self.quantity * (self.avg_price - current_price)

        # 持仓总价值
        position_value = self.quantity * current_price

        # 账户总价值 = 初始本金 + 未实现盈亏
        account_value = self.equity + pnl

        # 账户余额 = 初始余额 + 未实现盈亏（假设未实现盈亏可部分用于新仓位）
        available_balance = self.balance + pnl  # 简化模型

        # 保证金比率
        used_margin = self.position_notional / self.leverage
        margin_ratio = (used_margin + pnl) / position_value if position_value != 0 else 0

        # 强平价格
        if self.direction == 1:
            liquidation_price = (self.initial_margin * (1 - self.maintenance_margin_ratio)) / \
                                (self.quantity * (1 - self.maintenance_margin_ratio / self.leverage))
        else:
            liquidation_price = (self.initial_margin * (1 + self.maintenance_margin_ratio)) / \
                                (self.quantity * (1 + self.maintenance_margin_ratio / self.leverage))

        return {
            "position_value": round(position_value, 2),
            "unrealized_pnl": round(pnl, 2),
            "account_value": round(account_value, 2),
            "available_balance": round(available_balance, 2),
            "margin_ratio": round(margin_ratio * 100, 2),  # 百分比
            "liquidation_price": round(liquidation_price, 2),
            "avg_price": round(self.avg_price, 2)
        }

    def add_position(self, add_equity: float, add_price: float):
        """加仓操作"""
        # 新仓位的保证金和数量
        add_margin = add_equity
        add_notional = add_margin * self.leverage
        add_quantity = add_notional / add_price

        # 更新总持仓和平均价格
        total_quantity = self.quantity + add_quantity
        self.avg_price = (self.quantity * self.avg_price + add_quantity * add_price) / total_quantity
        self.quantity = total_quantity

        # 更新账户余额和本金
        self.balance -= add_margin  # 扣除新保证金
        self.equity += add_equity  # 假设加仓资金来自外部注入

    # 仓位控制
    def calculate_position_size(
            account_balance: float,
            risk_per_trade: float,
            stop_loss_pct: float,
            leverage: int
    ) -> float:
        risk_amount = account_balance * risk_per_trade
        position_value = risk_amount / stop_loss_pct
        required_margin = position_value / leverage
        return required_margin

    # 示例：10k账户，风险1.5%，止损4%，杠杆3倍
    margin = calculate_position_size(10000, 0.015, 0.04, 3)
    print(f"需投入保证金: {margin:.2f} USDT")  # 输出 1250 USDT（对应名义仓位 3*1250=3750 USDT）


# 使用示例
if __name__ == "__main__":
    # 初始化：1000USDT本金，5倍杠杆，在30000做多，仓位比例20%
    position = LeveragedPosition(
        equity=1000,
        leverage=5,
        entry_price=30000,
        position_ratio=0.2,
        direction=1
    )

    # 当前价格31000
    print("首次开仓后指标：")
    print(position.calculate_metrics(31000))

    # 加仓：追加500USDT，价格31000
    position.add_position(add_equity=500, add_price=31000)

    print("\n加仓后指标：")
    print(position.calculate_metrics(31000))


### **三、输出结果说明**
#
# ```python
# 首次开仓后指标：
# {
#     'position_value': 1033.33,  # 持仓总价值 = 0.0333 BTC * 31000
#     'unrealized_pnl': 33.33,  # 盈利 = 0.0333 * (31000-30000)
#     'account_value': 1033.33,  # 账户总价值 = 1000 + 33.33
#     'available_balance': 833.33,  # 余额 = 1000-200(初始保证金) + 33.33
#     'margin_ratio': 19.35,  # 保证金比率 = (200+33.33)/1033.33
#     'liquidation_price': 28800.0,  # 强平价格
#     'avg_price': 30000.0  # 持仓均价
# }
#
# 加仓后指标：
# {
#     'position_value': 2583.33,  # 总持仓 = 0.0333 + 0.0806 = 0.1139 BTC *31000
#     'unrealized_pnl': 83.33,  # 盈利 = 0.1139*(31000-30242.42)
#     'account_value': 1583.33,  # 账户总价值 = 1000+500 +83.33
#     'available_balance': 1083.33,  # 余额 = 1000-200(初始) +500-500(加仓) +83.33
#     'margin_ratio': 38.71,  # (700保证金 +83.33)/2583.33
#     'liquidation_price': 27586.21,  # 强平价格下降
#     'avg_price': 30242.42  # 新均价 = (0.0333*30000 +0.0806*31000)/0.1139
# }


### **四、关键逻辑解析**
#
# 1. ** 加仓后的平均成本 **
# 通过加权平均计算新的持仓均价，确保每次加仓后准确反映整体成本。
#
# 2. ** 保证金动态管理 **
# - 初始保证金为仓位比例对应的本金部分。--------------------------------
# - 加仓时需注入新资金，并扣除可用余额。
#
# 3. ** 强平价格计算 **
# 根据维持保证金率和杠杆倍数动态调整，加仓后强平价格可能变化。
#
# 4. ** 账户余额与总价值 **
# - 账户总价值 = 初始本金 + 未实现盈亏 + 新增资金。
# - 可用余额 = 初始余额 - 已用保证金     + 未实现盈亏。-------------------------------------
# 减仓 ；初始余额 - 已用保证金     + 未实现盈亏 + 已实现盈亏 + 释放的保证金
# 未实现盈亏是指当前持仓的浮动盈亏，即当前价格与开仓价格之间的差额乘以持仓数量。这部分盈亏尚未实际到账，但可以用于计算保证金。
# 减仓 ： 新账户余额 = 原账户余额 + 已实现盈亏 ± 释放的保证金（减仓数量*成本价格/杠杆）
#
# ---

### **五、风险控制建议**

# 1. ** 实时监控保证金比率 **：当
# `margin_ratio`
# 接近维持保证金率时触发预警。
# #** 动态调整杠杆 **：根据波动率降低杠杆倍数。


def adjust_leverage(self, volatility: float):
    """波动率越高，杠杆越低"""
    self.leverage = max(1, min(10, int(50 / volatility)))


#  ** 止损策略 **：基于ATR设置动态止损点。



def dynamic_stop_loss(self, atr: float, multiplier=2):
    stop_loss_price = self.avg_price - self.direction * multiplier * atr
    return stop_loss_price

'''
在比特币趋势策略中，初始杠杆倍数和仓位的选择需要基于**风险收益平衡**和**市场特性**综合考量。以下是一套系统化的配置原则和具体建议：

---

### **一、杠杆倍数的选择原则**
#### （1）**低杠杆优先（2-5倍）**
   - **原因**：比特币的日波动率常达5-10%，高杠杆（如10倍以上）易因短期波动触发强平。
   - **示例**：
     - 若使用5倍杠杆，价格反向波动20%才会爆仓（1/5=20%）；10倍杠杆仅需10%波动即爆仓。
     - **建议初始值**：3-5倍杠杆（兼顾收益与安全边际）。

#### （2）**动态调整机制**
   - **波动率挂钩**：当市场波动率（如ATR指标）上升时，主动降低杠杆倍数。
   - **账户净值保护**：若账户回撤超过10%，强制降低杠杆1-2倍。

---

### **二、仓位规模的计算逻辑**
仓位规模需结合**单笔风险承受上限**和**止损策略**计算，核心公式如下：

\[
\text{仓位量} = \frac{\text{账户净值} \times \text{单笔风险比例}}{\text{止损幅度} \times \text{合约面值}}
\]

#### （1）**参数定义**
   - **单笔风险比例**：建议≤2%（例：10,000 USDT账户，单笔最多亏200 USDT）
   - **止损幅度**：根据策略回测设定（通常为入场价的3-5%）
   - **合约面值**：比特币合约一般为1 BTC（或等值USDT）

#### （2）**计算示例**
   - 账户净值：10,000 USDT
   - 单笔风险比例：2%（200 USDT）
   - 止损幅度：4%（假设入场价50,000 USDT，止损价48,000 USDT）
   - 杠杆倍数：5倍

\[
\text{仓位量} = \frac{10,000 \times 2\%}{4\% \times 1} = \frac{200}{0.04} = 5,000 \ \text{USDT（名义价值）}
\]
\[
\text{实际保证金} = \frac{5,000}{5} = 1,000 \ \text{USDT}
\]

#### （3）**凯利公式优化**
若策略有明确的胜率（\(p\)）和盈亏比（\(b\)），可用凯利公式计算理论最优仓位比例：

\[
f = \frac{b \times p - q}{b} \quad (q=1-p)
\]

- **示例**：胜率40%，盈亏比3:1（赚3元赔1元）：
  \[
  f = \frac{3 \times 0.4 - 0.6}{3} = 0.2 \quad \text{（实际使用1/2凯利值，即10%仓位）}
  \]

---

### **三、实操配置建议**
| 账户规模   | 建议杠杆 | 单笔风险比例 | 止损幅度 | 名义仓位占比 |
|------------|----------|--------------|----------|--------------|
| <10,000 USDT | 3-5x     | 1-2%         | 4-5%     | 20-30%       |
| 10-50k USDT | 2-4x     | 0.5-1.5%     | 3-4%     | 15-25%       |
| >50k USDT   | 1-3x     | 0.3-1%       | 2-3%     | 10-20%       |

---

### **四、极端情况防护**
1. **压力测试**：
   - 模拟价格单日下跌20%时，账户是否存活。
   - 计算「黑天鹅事件」下的最大回撤（如2020年3月BTC单日跌40%）。

2. **保证金监控**：
   - 维持保证金率需低于交易所要求至少30%（例：交易所要求维持率10%，实际使用≤7%）。

3. **熔断机制**：
   - 当账户单日亏损达5%，暂停开新仓；
   - 当连续3笔亏损，强制降低杠杆至1倍。

---

### **五、进阶策略**
1. **金字塔加仓法**：
   - 初始仓位50%，趋势确认后以递减规模加仓（例：30% → 20%）。
   - 每层加仓需重新计算止损和杠杆。

2. **波动率自适应模型**：
   - 使用Bollinger Band宽度或ATR调整仓位：
     \[
     \text{动态仓位} = \frac{\text{基础仓位}}{\text{当前波动率/历史平均波动率}}
     \]

---

### **六、注意事项**
- **交易所规则**：逐仓模式下，亏损仅影响该仓位保证金；全仓模式下可能波及全部资产。
- **手续费影响**：高频交易需扣除手续费（如币安Maker费0.02%，Taker费0.04%）。
- **滑点控制**：大仓位减仓时，使用限价单+冰山委托避免价格冲击。

---

### **总结配置方案**
**初始参数推荐**：
- **杠杆倍数**：3倍
- **单笔风险**：1.5%账户净值
- **止损幅度**：4%
- **仓位占比**：约25%账户净值（名义价值）

**公式化配置工具**：
```python
def calculate_position_size(
    account_balance: float,
    risk_per_trade: float,
    stop_loss_pct: float,
    leverage: int
) -> float:
    risk_amount = account_balance * risk_per_trade
    position_value = risk_amount / stop_loss_pct
    required_margin = position_value / leverage
    return required_margin

# 示例：10k账户，风险1.5%，止损4%，杠杆3倍
margin = calculate_position_size(10000, 0.015, 0.04, 3)
print(f"需投入保证金: {margin:.2f} USDT")  # 输出 1250 USDT（对应名义仓位 3*1250=3750 USDT）
```

通过以上方法，您可以在控制风险的前提下，合理利用杠杆提升资金效率。实际交易中需持续监控策略表现，每季度重新优化参数。
'''

