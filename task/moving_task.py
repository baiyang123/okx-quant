from strategy.moving import moving


def moving_task(*args):
    current_app = args[0]
    moving_service = moving(context=current_app.app_context())
    moving_service.strategy()
