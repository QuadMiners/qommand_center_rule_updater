import json
import logging

from google.protobuf import json_format
from termcolor import cprint

import command_center.library.database as db
from command_center.library.AppLibrary import sql_replace
from command_center.protocol.data.data_pb2 import DataLevel

logger = logging.getLogger(__name__)


class SnortMixin(object):
    def status_insert(self, version, rule_status):
        status_dict = json_format.MessageToDict(rule_status)
        status_dict['tags'] = "{}"
        query = """
        INSERT INTO rule_status (version,target_version,type,state,name,tags,created_at,updated_at,delete_flag)
        VALUES('{version}','{target_version}','{type}','{state}','{name}','{tags}','{created_at}','{updated_at}','{delete_flag}')
        ON CONFLICT (version, type, state)
        DO UPDATE SET 
            target_version = excluded.target_version,
            name = excluded.name,
            tags= excluded.tags,
            created_at= excluded.created_at,
            updated_at= excluded.updated_at,
            delete_flag= excluded.delete_flag
        RETURNING id;
        """.format(**status_dict)
        cprint(query)

        status_id = db.pmdatabase.execute(query, returning_id=True)
        return status_id

    def snort_insert(self, rule_status_id,version, datas, data_level=DataLevel.L_UPDATE):
        master_query = """
                INSERT INTO rule_master_hunt (enabled,action,header,proto,src_ip,src_port,direction,dst_ip,dst_port,"group",gid,rev,msg,flowbits,metadata,"references",classtype,priority,options,raw,sid,version,sha1,type,provider,created_at,updated_at,rule_status_id)
                VALUES('{enabled}','{action}','{header}','{proto}','{src_ip}','{src_port}','{direction}','{dst_ip}','{dst_port}','{group}','{gid}','{rev}','{msg}',{flowbits},{metadata},{references},'{classtype}','{priority}','{options}','{raw}','{sid}','{version}','{sha1}','{type}','{provider}', '{created_at}','{updated_at}','{rule_status_id}')
                ON CONFLICT (sid, rule_status_id) 
                DO UPDATE SET
                 enabled = excluded.enabled , 
                 action = excluded.action,
                 header=excluded.header,
                 proto=excluded.proto,src_ip=excluded.src_ip,src_port=excluded.src_port,
                 direction=excluded.direction,dst_ip=excluded.dst_ip,dst_port=excluded.dst_port,
                 "group"=excluded.group,
                 gid=excluded.gid,
                 rev=excluded.rev,msg=excluded.msg,
                 flowbits=excluded.flowbits,
                 metadata=excluded.metadata,
                 "references"=excluded.references,
                 classtype=excluded.classtype,
                 priority=excluded.priority,
                 options=excluded.options,
                 raw=excluded.raw,
                 sid=excluded.sid,
                 version=excluded.version,
                 sha1=excluded.sha1,
                 type=excluded.type,
                 provider=excluded.provider,
                 created_at=excluded.created_at,
                 updated_at=excluded.updated_at,
                 rule_status_id=excluded.rule_status_id
              """

        master_history_query = """
                INSERT INTO rule_master_hunt_history (enabled,action,header,proto,src_ip,src_port,direction,dst_ip,dst_port,"group",gid,rev,msg,flowbits,metadata,"references",classtype,priority,options,raw,sid,version,sha1,type,provider,created_at,updated_at,rule_status_id,merge_code)
                VALUES('{enabled}','{action}','{header}','{proto}','{src_ip}','{src_port}','{direction}','{dst_ip}','{dst_port}','{group}','{gid}','{rev}','{msg}',{flowbits},{metadata},{references},'{classtype}','{priority}','{options}','{raw}','{sid}','{version}','{sha1}','{type}','{provider}', '{created_at}','{updated_at}','{rule_status_id}', '{merge_code}')
                ON CONFLICT (sid, rule_status_id) 
                DO UPDATE SET
                 enabled = excluded.enabled , 
                 action = excluded.action,
                 header=excluded.header,
                 proto=excluded.proto,src_ip=excluded.src_ip,src_port=excluded.src_port,
                 direction=excluded.direction,dst_ip=excluded.dst_ip,dst_port=excluded.dst_port,
                 "group"=excluded.group,
                 gid=excluded.gid,
                 rev=excluded.rev,msg=excluded.msg,
                 flowbits=excluded.flowbits,
                 metadata=excluded.metadata,
                 "references"=excluded.references,
                 classtype=excluded.classtype,
                 priority=excluded.priority,
                 options=excluded.options,
                 raw=excluded.raw,
                 sid=excluded.sid,
                 version=excluded.version,
                 sha1=excluded.sha1,
                 type=excluded.type,
                 provider=excluded.provider,
                 created_at=excluded.created_at,
                 updated_at=excluded.updated_at,
                 merge_code=excluded.merge_code,
                 rule_status_id=excluded.rule_status_id
              """
        def array_field(ar_data):
            if ar_data:
                ret_data = sql_replace(str({ k for k in ar_data}).replace("'", '"'))
            else:
                ret_data = 'NULL'
            return ret_data

        """
            전체 가저오지 않고 변경된 정보만 가져올경우를 위해 모두 history 에 eq 로 쌓고, 변경된 정보만 반영한다.
            
        """
        self.master_hunt_history_eq_insert(version, rule_status_id)

        for data in datas:
            snort_dict = json_format.MessageToDict(data)
            snort_dict['rule_status_id'] = rule_status_id
            snort_dict['flowbits'] =array_field(snort_dict['flowbits'])
            snort_dict['metadata'] = array_field(snort_dict['metadata'])
            snort_dict['references'] = array_field(snort_dict['references'])

            if int(snort_dict['merge_code']) in [1,2,4]:
                temp_query = master_query.format(**snort_dict)
                cprint(temp_query)
                db.pmdatabase.execute(temp_query)
            elif int(snort_dict['merge_code']) in (3,):
                del_query = "DELETE FROM rule_master_hunt WHERE sid={0}".format(snort_dict['sid'])
                cprint(del_query)
                db.pmdatabase.execute(del_query)

            temp_query = master_history_query.format(**snort_dict)
            print(temp_query)
            db.pmdatabase.execute(temp_query)

        """
            master_hunt 버전정보를 바꿔준다. rule_status_id 에 해당하는 버전으로 전부 변경해준다.
            기존정보를 유지 하면서 변경하는것이어서 업데이트 해줘야함.
        """
        db.pmdatabase.execute("UPDATE rule_master_hunt SET rule_status_id ={0}, version = {1}".format(rule_status_id,version))

    def master_hunt_history_eq_insert(self, version, rule_status_id):
        query = """
        INSERT INTO rule_master_hunt_history (enabled,action,header,proto,src_ip,src_port,direction,dst_ip,dst_port,"group",gid,rev,msg,flowbits,metadata,"references",classtype,priority,options,raw,sid,version,sha1,type,provider,merge_code,created_at,updated_at,rule_status_id)
        SELECT enabled,action,header,proto,src_ip,src_port,direction,dst_ip,dst_port,"group",gid,rev,msg,flowbits,metadata,"references",classtype,priority,options,raw,sid,{0},sha1,type,provider,1,created_at,updated_at,{1}
        FROM rule_master_hunt
        ON CONFLICT (sid, rule_status_id) 
        DO UPDATE SET
             enabled = excluded.enabled , 
             action = excluded.action,
             header=excluded.header,
             proto=excluded.proto,src_ip=excluded.src_ip,src_port=excluded.src_port,
             direction=excluded.direction,dst_ip=excluded.dst_ip,dst_port=excluded.dst_port,
             "group"=excluded.group,
             gid=excluded.gid,
             rev=excluded.rev,msg=excluded.msg,
             flowbits=excluded.flowbits,
             metadata=excluded.metadata,
             "references"=excluded.references,
             classtype=excluded.classtype,
             priority=excluded.priority,
             options=excluded.options,
             raw=excluded.raw,
             sid=excluded.sid,
             version=excluded.version,
             sha1=excluded.sha1,
             type=excluded.type,
             provider=excluded.provider,
             created_at=excluded.created_at,
             updated_at=excluded.updated_at,
             merge_code=excluded.merge_code,
            rule_status_id=excluded.rule_status_id

        """.format(version, rule_status_id)
        print(query)
        db.pmdatabase.execute(query)