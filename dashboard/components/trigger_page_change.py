from dash import Input


ID_TRIGGER_PAGE_CHANGE = "trigger-params-preferences"


def add_watcher_params_preferences():
    return Input(ID_TRIGGER_PAGE_CHANGE, "data", True)
