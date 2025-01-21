# okx-quant
本项目为okx量化项目，兼顾完整量化体系，祝大家共同进步，共同学习沟通，欢迎大家沟通
项目介绍：
0. 运行请先 pip install -r requirements.txt
1. 回测总触发器为backtesting目录下back_testing
2. 策略为strategy目录
3. 先通过MarketFactory().get_history_data('BTC-USDT-SWAP', '2023-03-05', '2024-11-05', '1D')获取历史数据，再去跑回测
4. 封装的方法在factory下
5. 此项目会不断的封装，优化

量化自学顺序：看本项目的同学需要已经掌握panda库的一些基本操作，如未掌握可先学习本人另一个项目quant
1. 对接所有okxapi www.okx.com
2. 先写一个回测策略，并用pyplot欣赏自己的作品，并记录每一周期的操作，本项目把操作以及临时历史数据放在csv文件中
3. 对接实盘
4. 联通实盘后跑模拟盘
5. 跑实盘
2345的过程中需要不断的优化提取公共方法。截止到此量化学习的入门就完成了，接下来就是漫长的，自律的，寻找能赚钱的策略（不断重复2,4，5）前一步结果好后进入后一步
6. 终极奥义：寻找money   

作者：ybai 具体学习沟通初次可通过邮箱1006925476@qq.com取得联系


2024进度
趋势+网格两个策略的模拟盘以及回测
但目前两个策略各有缺点，一个适合趋势一个适合震荡，目前的行情网格效果很好
2025目标
1. 解耦，整合代码
2. 写出满意的策略，初步计划为找到切换两个策略的指标然后将两个策略结合

无线网格待解决问题： 1. 如果一直涨仓位越来越小怎么办 2. 如果一直涨导致持仓方向反了怎么办