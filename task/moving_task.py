from strategy.moving import moving
from strategy.grid_inf import GridInf

def moving_task(*args):
    current_app = args[0]
    moving_service = moving(context=current_app.app_context())
    moving_service.strategy()

def grid_inf_task(*args):
    current_app = args[0]
    grid_inf_service = GridInf()
    grid_inf_service.strategy()
