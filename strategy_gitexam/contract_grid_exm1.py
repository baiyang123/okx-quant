# https://github.com/fmzquant/strategies/blob/87a415edf7b08065fbcbfbfefb7351cd929e4dbd/%E7%AE%80%E6%98%93%E7%AD%89%E5%B7%AE%E5%90%88%E7%BA%A6%E7%BD%91%E6%A0%BC.md?plain=1#L4

# > Name
#
# 简易等差合约网格
#
# > Author
#
# 诺宝
#
# > Strategy
# Description
#
# ** 参数非常简单，以BTC为例，到了开多的区域平空买底仓开多，到了开空的区域平多买底仓开空，反复轮回 **
# ** 显然，在币圈，从长期来看，任何复杂模型都跑不过无脑网格 **
# ** 财富密码是无脑网格 + 无脑梭哈土狗 **
# ** 希望和最早的马丁一样，都是最为简单粗暴但是赚钱的策略 **
# ![IMG](https: // www.fmz.com / upload / asset / 1
# bdae37080236f7ea7077.png)
#
# > Strategy
# Arguments
#
# | Argument | Default | Description |
# | ---- | ---- | ---- |
# | M | 20 | 杠杆大小 |
# | H | 50 | 初始底仓份数 |
# | n1 | true | 单个网格交易数量 |
# | grid | 200 | 单个网格交易间距 |
# | xia | 35000 | 开多点位 |
# | shang | 60000 | 开空点位 |
#
# > Source(python)
#
# ``` python
'''backtest
start: 2021-01-01 00:00:00
end: 2021-11-17 00:00:00
period: 1m
basePeriod: 1m
exchanges: [{"eid":"Futures_Binance","currency":"BTC_USDT","balance":2500}]
args: [["H",30],["n1",0.001],["grid",300],["xia",50000]]
'''

# 做网格，为什么减仓加仓要调删除所有未完成订单订单：到了开多的区域平空买底仓开多，到了开空的区域平多买底仓开空


def CancelPendingOrders(): # 有未完成的订单全部取消
    orders = _C(exchanges[0].GetOrders)
    if len(orders) > 0:
        for j in range(len(orders)):
            exchanges[0].CancelOrder(orders[j].Id, orders[j])
            j = j + 1


def main():
    exchange.SetContractType('swap')
    exchange.SetMarginLevel(M)
    currency = exchange.GetCurrency()
    if _G('buyp') and _G('sellp'):
        buyp = _G('buyp') # 配置开空点位，开多点位，这里后续是应该可以自动算出来
        sellp = _G('sellp')
        Log('读取网格价格')
    else:
        ticker = exchange.GetTicker()
        buyp = ticker["Last"] - grid # 最新成交价+单网交易间距，第一个bs网点
        sellp = ticker["Last"] + grid
        _G('buyp', buyp)
        _G('sellp', sellp)
        Log('网格数据初始化')
    while True:
        account = exchange.GetAccount()
        ticker = exchange.GetTicker()
        position = exchange.GetPosition()
        orders = exchange.GetOrders()
        if len(position) == 0: # 无仓先入底仓 根据开孔点位决定底仓是空头还是多头
            if ticker["Last"] > shang: # 开空点位
                exchange.SetDirection('sell')
                exchange.Sell(-1, n1 * H)  # 单笔下单数量*杠杆
                Log(currency, '到达开空区域,买入空头底仓')

            else:
                exchange.SetDirection('buy')
                exchange.Buy(-1, n1 * H)
                Log(currency, '到达开多区域,买入多头底仓')
        if len(position) == 1:
            if position[0]["Type"] == 1:  # 1为空单
                if ticker["Last"] < xia:  # 在开多点位之下
                    Log(currency, '空单全部止盈反手')  # 到达下 ，止盈空单
                    exchange.SetDirection('closesell')
                    exchange.Buy(-1, position[0].Amount)
                else:
                    orders = exchange.GetOrders()
                    if len(orders) == 0:
                        exchange.SetDirection('sell')
                        exchange.Sell(sellp, n1)
                        exchange.SetDirection('closesell')
                        exchange.Buy(buyp, n1)
                    if len(orders) == 1: # 如果有成交单
                        if orders[0]["Type"] == 1:  # 空单止盈成交
                            Log(currency, '网格减仓,当前份数:', position[0].Amount)
                            CancelPendingOrders()
                            buyp = buyp - grid # 重新设置下一个买卖点
                            sellp = sellp - grid
                            LogProfit(account["Balance"])
                        if orders[0]["Type"] == 0: # 如果当前下单是多单有未完成的，则加仓
                            Log(currency, '网格加仓,当前份数:', position[0].Amount)
                            CancelPendingOrders()
                            buyp = buyp + grid
                            sellp = sellp + grid
                            LogProfit(account["Balance"])

            if position[0]["Type"] == 0: # 多单已经超过了上点位
                if ticker["Last"] > float(shang):
                    Log(currency, '多单全部止盈反手')
                    exchange.SetDirection('closebuy')
                    exchange.Sell(-1, position[0].Amount)
                else:
                    orders = exchange.GetOrders()
                    if len(orders) == 0: #没有未成交的单子就下单，有就把不应该成交的单子取消了
                        exchange.SetDirection('buy')
                        exchange.Buy(buyp, n1)
                        exchange.SetDirection('closebuy')
                        exchange.Sell(sellp, n1)
                    if len(orders) == 1:
                        if orders[0]["Type"] == 0:  # 止盈成交   买是0卖是1
                            Log(currency, '网格减仓,当前份数:', position[0].Amount)
                            CancelPendingOrders()
                            buyp = buyp + grid
                            sellp = sellp + grid
                            LogProfit(account["Balance"])
                        if orders[0]["Type"] == 1:
                            Log(currency, '网格加仓,当前份数:', position[0].Amount)
                            CancelPendingOrders()
                            buyp = buyp - grid
                            sellp = sellp - grid
                            LogProfit(account["Balance"])




# https://www.fmz.com/strategy/330440   发明者量化 App


'''
此策略好像是无线合约网格，可做成无线做多合约网格
-1为市单价
exchange.Buy	"buy"	买入开多仓
exchange.Buy	"closesell"	买入平空仓
exchange.Sell	"sell"	卖出开空仓
exchange.Sell	"closebuy"	卖出平多仓
初始buyp和sellp为买一卖一价格加减单网格间距
1. 无仓则根据是否在多头领域开底仓 决定了本轮是多还是空  初始底仓分数乘以单网格交易数量，市价开仓，初始化上下买卖点差一个网格
2. 有多仓位，则大于上点位，多长全部止盈
3. 否则如果当前没有未完成的单子则设置方向为买，买一价格买入单网格交易数量，设置方向为买完了，然后下卖单为最新成交价格+单网价格，如果有成交则赚了一个网格的钱
4. 如果有未完成的单子，如果有多多单，取消当前多单，并设置网格买卖点提升一个格子，
'''

'''
高频：此策略不是提前埋单，而是下了底仓之后不停的根据方向去套利，如果单方向涨底仓会越来越少，震荡的话会保持底仓，但如果震荡之后把自己的成本提高后，再但方面下跌的话也可以无线套利，直到把底仓的亏损覆盖，-------------这里要算好下点位多少可以承受总仓位百分之5（不算杠杆的损失，这里指的是做多合约）
1. 下完初始单后，如果没有挂单，则下买卖单上下差一个网格
2. 如果被干掉了一个方向的单子，看 剩下的单子是买的还是卖的，如果试买单，说明卖单止盈成交了，价格涨了，网格减过一笔仓，这时取消掉价格低的买单，重新设置网格提升一个网格，这时没有单子了，触发了if len(orders)==0:，再下一对买卖单等着被吃掉一个方向后决定是上移网格还是下移网格
3. 如果两边都没吃掉就过
思考：
1. 如果上移了之后还是没有赶上，那他的市单价会被高价吃掉，慢慢直到把底仓卖光，---------------这里要计算的是到底底仓放多少合适，到了上点位全部止盈，至少要能卖到上点位
2. 如果瞬间把上下全吃了，重新下上下点位，下一次循环会剩下一个，仍然无线循环
3. 开多的话，要计算平仓点位，不能高于下点位
12,23，原理搞懂，要想一想具体各个数值设置多少比较好，其实两个思考项就是如何不亏超过承受5个点损失，以及如何保证一直涨一直有仓位，这里做多合约可以不设止盈只设下线，通过无线套利不怕下跌，止损线无线降低，无线收益，
思考：----------1. 是否设置最大回撤重新放底仓这样是否会失去廉价筹码容易触发止损，不然一直单方面下跌会吃掉利润，如果重新开仓重新计算的话似乎需要择时 不能一直做，因为有杠杆还不如保留底仓
-----------2. 如果未做择时则保留底仓，如果做了择时则可重新开仓（为计算成本或者利润也可以留下最低仓位一手）
----------3. 这样比提前埋单好，这样可以无线网格，而且不会因为提前埋单占用过多的仓位
4. 到底是单多好还是多空双向好，根据实验可能是双向好
5. 这里全部止盈之后（超过预设的上下线）策略就停止了么
'''


'''
场景1：在上线上买入空单后一直涨，不停的用网格差价，底仓不会丢失会一直亏直到爆仓，所以在上下线外还应该有一个平仓线
'''

'''
网格要素：
0. k线周期：暂定日线  1Dutc
1. 多空线（开多点位开空点位） ：暂定布林线  布林中线开底仓（20日） get_grid_info boll_info
2. 止盈止损线 计算出总仓位实际亏损20个点止损，止损后重新导布林中线建仓，（考虑是否要止盈）（每次现算亏损比例）
3. 网格数（无线网格可以没有这个）
4. 网格间距 进20日平均波动的倍数，先用一倍来做，每次成交后现算  atr
5. 初始底仓份数  一半？或者5分之1？
6. 每个网格交易数 百分之5？
7. 杠杆 先做5倍杠杆
8. 先按照上述数据写后进行测试
'''