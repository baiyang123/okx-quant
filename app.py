from flask import Flask
from flask_apscheduler import APScheduler
from task.moving_task import moving_task

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'


def init_app(profile_path):
    # 获取配置文件
    app.config.from_pyfile(profile_path)
    task_switch = app.config.get("TASK_SWITCH")
    # 开启定时任务
    if task_switch:
        scheduler = APScheduler()
        scheduler.init_app(app)

        # ma任务
        scheduler.add_job(func=moving_task, trigger='cron', day='*', hour='*', minute='00', second='00',
                          id='moving_task_01', args=[app])

        # 样例
        # scheduler.add_job(func=hrm_entry_task, trigger='cron', day="*", hour='*', minute='*', second='30',
        #                   id='hrm_entry_task', args=[app])

        # scheduler.add_job(func=contract_grid_work, trigger='interval', seconds=30,
        #                   id='contract_grid_work', args=[app])

        scheduler.start()


if __name__ == '__main__':
    init_app("config.py")
    app.run()
