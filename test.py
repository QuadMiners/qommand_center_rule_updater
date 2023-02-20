from rule_updater.env import get_env_int

print(type(get_env_int('HEARTBEAT_TIME')))
print(get_env_int('VERSION_CHECK_TIME'))
