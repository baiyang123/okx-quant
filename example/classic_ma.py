/*backtest
start: 2019-01-01 00:00:00
end: 2019-07-01 00:00:00
period: 1d
exchanges: [{"eid":"Bitfinex","currency":"BTC_USD"}]
*/

# fmz案例学习

function main() {
    var STATE_IDLE  = -1;
    var state = STATE_IDLE;
    var entryPrice = 0;
    var initAccount = _C(exchange.GetAccount);
    Log(initAccount);
    while (true) {
        if (state === STATE_IDLE) {
            var n = $.Cross(FastPeriod, SlowPeriod);
            if (Math.abs(n) >= EnterPeriod) {
                var account = _C(exchange.GetAccount);
                var ticker = _C(exchange.GetTicker);
                var obj = n > 0 ? $.Buy(_N(account.Balance * PositionRatio / ticker.Sell, 3)) : $.Sell(_N(account.Stocks * PositionRatio, 3));
                if (obj) {
                    opAmount = obj.amount;
                    entryPrice = obj.price;
                    state = n > 0 ? PD_LONG : PD_SHORT;
                    Log("开仓详情", obj, "交叉周期", n);
                }
            }
        } else {
            var n = $.Cross(ExitFastPeriod, ExitSlowPeriod);
            var needCover = Math.abs(n) >= ExitPeriod && ((state === PD_LONG && n < 0) || (state === PD_SHORT && n > 0));
            if (needCover) {
                Log("离市平仓");
            } else {
                var ticker = _C(exchange.GetTicker);
                if (state === PD_LONG) {
                    if (ticker.Buy < entryPrice*(1-StopLossRatio)) {
                        needCover = true;
                        Log("止损平仓");
                    }
                } else {
                    if (ticker.Sell > entryPrice*(1+StopLossRatio)) {
                        needCover = true;
                        Log("止损平仓");
                    }
                }
            }
            if (needCover) {
                var nowAccount = _C(exchange.GetAccount);
                var obj = state === PD_LONG ? $.Sell(_N(nowAccount.Stocks - initAccount.Stocks, 3)) : $.Buy(_N(initAccount.Stocks - nowAccount.Stocks, 3));
                state = STATE_IDLE;
                nowAccount = _C(exchange.GetAccount);
                LogProfit(nowAccount.Balance - initAccount.Balance, '钱:', nowAccount.Balance, '币:', nowAccount.Stocks, '平仓详情:', obj, "交叉周期", n);
            }
        }
        Sleep(Interval*1000);
    }
}