# idstools~=0.6.4 을 사용하여 Snort룰을 파싱하는 클래스

import hashlib

from idstools.rule import Rule, parse, parse_file

example_line = 'alert tcp [1.233.206.27,1.55.215.71,101.108.105.88,101.33.80.197,101.36.108.161,101.36.118.6,' \
               '101.53.100.155,102.130.123.208,102.219.33.86,102.220.77.155,102.67.239.240,103.10.171.14,' \
               '103.10.87.101,103.107.9.61,103.110.84.163,103.115.24.11,103.119.3.240,103.120.82.30,103.13.40.2,' \
               '103.133.120.4,103.133.27.254,103.145.27.1,103.146.140.152,103.147.4.105,103.150.60.6,103.152.18.138,' \
               '103.156.68.195,103.158.212.246,103.161.39.169,103.164.221.210,103.17.48.8,103.179.57.205,' \
               '103.181.142.170,103.181.143.143,103.183.74.28,103.19.56.102,103.206.170.16,103.214.229.236,' \
               '103.215.222.178,103.219.0.49,103.237.145.23,103.241.178.2,103.26.136.173,103.37.83.26,103.38.252.76,' \
               '103.46.238.142,103.48.193.7,103.60.101.114,103.72.6.149,103.78.88.51] any -> $HOME_NET any (msg:"ET ' \
               '3CORESec Poor Reputation IP TCP group 1"; flags:S; reference:url,' \
               'blacklist.3coresec.net/lists/et-open.txt; threshold: type limit, track by_src, seconds 3600, ' \
               'count 1; classtype:misc-attack; sid:2525000; rev:639; metadata:affected_product Any, attack_target ' \
               'Any, deployment Perimeter, tag 3CORESec, signature_severity Major, created_at 2020_07_20, updated_at ' \
               '2022_12_30;)'

aaa = Rule()

def parse_line(p_rule_line: str):
    linea = p_rule_line.rstrip()
    rule = parse(linea)
    return rule

rule = parse_line(example_line)
print(rule['action'], type(rule))

rule_obj = parse_file("sql.rules")
print(rule_obj[1])
print(rule_obj[2])
print(type(rule_obj[3]))
print(dict(rule_obj[4]))
print(rule_obj[5]["raw"])


def __generate_sha1_line(self, line):
    if isinstance(line, bytes):
        line = line.decode()
    line = line.rstrip()
    buf = line.encode()
    sha = hashlib.sha1()
    sha.update(buf)

    # return sha.hexdigest(), len(line), line
    return int(sha.hexdigest(), 16) % (10 ** 8), len(line), line


