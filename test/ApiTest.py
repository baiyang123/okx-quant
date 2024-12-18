import requests

LOCALHOST = 'https://www.okx.com'

# 验证网络联通性
def test_market_tickers():
    url = LOCALHOST + "/api/v5/public/instruments?instId=BTC-USDT-SWAP&instType=SWAP"
    param = {}
    headers = {}
    response = requests.request("get", url, headers=headers, json=param)
    print(response.text)

# 如果需要代理 https://docs.ne.world/win/clash/  bing.com 搜设置cmd代理 request库http socks代理  地址127.0.0.1端口7890
proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}


# 验证网络联通性
def test_market_tickers_proxies():
     url = LOCALHOST + "/api/v5/public/instruments?instId=BTC-USDT-SWAP&instType=SWAP"

     response = requests.request('get', url, proxies=proxies)
     print(response.text)

if __name__ == '__main__':
    test_market_tickers()