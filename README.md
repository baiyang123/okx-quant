本项目为okx量化项目，兼顾完整量化体系，祝大家共同进步，共同学习沟通，欢迎大佬指点，微信by1006925476
0. 运行请先 pip install -r requirements.txt
1. 回测总触发器为backtesting目录下back_testing
2. 策略为strategy目录
3. 先通过MarketFactory().get_history_data('BTC-USDT-SWAP', '2023-03-05', '2024-11-05', '1D')获取历史数据，再去跑回测
