from dash import Input, Output, dcc


ID_AUTH_TOKEN = "token_user"


def add_input_auth_token():
    return Input(ID_AUTH_TOKEN, "data", True)


def add_output_auth_token():
    return Output(ID_AUTH_TOKEN, "data", True)


stores = [dcc.Store(ID_AUTH_TOKEN, "session")]
