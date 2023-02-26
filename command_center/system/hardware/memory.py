import subprocess
from functools import lru_cache


@lru_cache(maxsize=2048)
def get_memory_info():
    # lshw -short -C memory 명령어를 이용한 리눅스 Memory 정보 가져오기
    try:
        p = subprocess.Popen(["lshw -short -C memory"], stdout=subprocess.PIPE, shell=True)
        result = p.communicate()[0].decode("utf-8").split('\n')
        total_info = list(filter(lambda x:'System Memory' in x, result))[0].split()
        hw_path = total_info[0]
        total_memory = total_info[2]
        bank_info_list = list(filter(lambda x:hw_path in x and x.split()[0]!=hw_path, result))
    except:
        return None
    return {
        "hw_path": hw_path,
        "total_memory": total_memory,
        "bank_info_list" : bank_info_list,
    }

