import os
from dotenv import load_dotenv

load_dotenv()


def get_env_int(p_str: str):
    return int(os.environ.get(p_str))


def get_env_str(p_str: str):
    return os.environ.get(p_str)
