import os
from dotenv import load_dotenv

load_dotenv()


def get_env_int(p_str: str):
    return int(os.environ.get(p_str))
