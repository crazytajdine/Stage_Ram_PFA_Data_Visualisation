# dashboard/state.py
from data_managers.session_manager import SessionManager
session_manager = SessionManager()  # uses Redis if available, else memory
