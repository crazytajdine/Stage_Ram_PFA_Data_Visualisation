# filter_state.py
_filter_state = {}

def set_filter_state(filters: dict):
    global _filter_state
    _filter_state = filters or {}

def get_filter_state() -> dict:
    return _filter_state
