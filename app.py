from flask import Flask
from flask_apscheduler import APScheduler
from task.moving_task import moving_task, grid_inf_task
from loguru import logger

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'

'''
**Executor 如果是默认的 10 个容量的线程池，恰好 10 个线程都在忙，恰好又有一个任务该执行了，由于没有空闲线程来处理，这个任务将被抛弃。**这个问题就比较常见了，
也是我遇到问题的罪魁祸首。如果是因为没有线程处理导致的定时任务不执行，那么会输出日志：
Run time of job "xxx (trigger: cron[year='*', month='*', day='*', day_of_week='*', hour='*', minute='*', second='*'], next run at: 2024-01-05 11:17:37 CST)" was missed by 0:00:05.255671，抓住关键词：was missed by，
那么基本上就是这个问题了。
适当加大线程池大小，并在创建任务的时候加上 misfire_grace_time 参数。
'''
def init_app(profile_path):
    # 获取配置文件
    app.config.from_pyfile(profile_path)

    logger.add("logs/logfile_{time:YYYY-MM-DD}.log", level="INFO", rotation="1 day")

    task_switch = app.config.get("TASK_SWITCH")
    # 开启定时任务
    if task_switch:
        scheduler = APScheduler()
        scheduler.init_app(app)
        # ma任务
        # # 当任务被唤起时，如果在 misfire_grace_time 时间差内，依然运行。
        # back_scheduler.add_job(... , misfire_grace_time=30)
        # 每个任务都有一个 misfire_grace_time，单位：秒，默认是 0 秒。意思是那些错过的任务在有条件执行时（有线程空闲出来/服务已恢复），如果还没有超过 misfire_grace_time，就会被再次执行。如果 misfire_grace_time=None，就是不论任务错过了多长时间，都会再次执行。
        scheduler.add_job(func=grid_inf_task, trigger='cron', day='*', hour='*', minute='*',
                          id='grid_inf_task_01', args=[app], misfire_grace_time=30)

        # 样例
        # scheduler.add_job(func=hrm_entry_task, trigger='cron', day="*", hour='*', minute='*', second='30',
        #                   id='hrm_entry_task', args=[app])

        # scheduler.add_job(func=contract_grid_work, trigger='interval', seconds=30,
        #                   id='contract_grid_work', args=[app])

        scheduler.start()


if __name__ == '__main__':
    init_app("config.py")
    app.run()
