import requests

LOCALHOST = 'https://www.okx.com'

# 验证网络联通性
def test_market_tickers():
    url = LOCALHOST + "/api/v5/public/instruments?instId=BTC-USDT-SWAP&instType=SWAP"
    param = {}
    headers = {}
    response = requests.request("get", url, headers=headers, json=param)
    print(response.text)