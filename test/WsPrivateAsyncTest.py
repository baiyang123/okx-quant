import asyncio

from okx.websocket.WsPrivateAsync import WsPrivateAsync


def privateCallback(message):
    print("privateCallback", message)


async def main():
    # wss://wspap.okex.com:8443/ 为测试环境
    # url = "wss://wseea.okx.com:8443/ws/v5/private?brokerId=9999"
    url = "wss://ws.okx.com:8443/ws/v5/private"
    api_key = 'd759cf97-a1b3-40da-9c49-911629d7b3b6'
    api_secret_key = 'C8C89E3E0D6FA34530F1BBD2C33DFDBF'
    passphrase = ''
    ws = WsPrivateAsync(
        apiKey=api_key,
        passphrase=passphrase,
        secretKey=api_secret_key,
        url=url,
        useServerTime=False
    )
    await ws.start()
    args = []
    # 获取账户信息，首次订阅按照订阅维度推送数据，此外，当下单、撤单、成交等事件触发时，推送数据以及按照订阅维度定时推送数据
    arg1 = {"channel": "account", "ccy": "BTC"}
    # 获取订单信息，首次订阅不推送，只有当下单、撤单等事件触发时，推送数据
    arg2 = {"channel": "orders", "instType": "ANY"}
    # 获取账户余额和持仓信息，首次订阅按照订阅维度推送数据，此外，当成交、资金划转等事件触发时，推送数据。
    #
    # 该频道适用于尽快获取账户现金余额和仓位资产变化的信息。
    arg3 = {"channel": "balance_and_position"}
    args.append(arg1)
    args.append(arg2)
    args.append(arg3)
    print("-----------------------------------------subscribe--------------------------------------------")
    await ws.subscribe(args, callback=privateCallback)
    await asyncio.sleep(30)
    print("-----------------------------------------unsubscribe--------------------------------------------")
    args2 = [arg2]
    # await ws.unsubscribe(args2, callback=privateCallback)
    # await asyncio.sleep(30)
    # print("-----------------------------------------unsubscribe all--------------------------------------------")
    # args3 = [arg1, arg3]
    # await ws.unsubscribe(args3, callback=privateCallback)


if __name__ == '__main__':
    asyncio.run(main())
