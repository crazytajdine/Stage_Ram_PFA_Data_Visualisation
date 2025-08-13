from dash import Input, Output, dcc


ID_TRIGGER_PAGE_CHANGE = "trigger-params-preferences"


def add_input_manual_trigger():
    return Input(ID_TRIGGER_PAGE_CHANGE, "data", True)


def add_output_manual_trigger():
    return Output(ID_TRIGGER_PAGE_CHANGE, "data", True)


stores = [dcc.Store(ID_TRIGGER_PAGE_CHANGE)]
