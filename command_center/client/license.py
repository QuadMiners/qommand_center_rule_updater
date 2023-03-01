import logging

from command_center.client import ClientRequestMixin
from command_center.library.rpc.retry import retrying_stub_methods
from command_center.protocol import rule_update_service_pb2_grpc
from command_center.protocol.license import license_pb2
from command_center.protocol.license.license_pb2 import LicenseRegistrationRequest
from command_center.library.AppConfig import gconfig

import command_center.library.database as db

logger = logging.getLogger(__name__)


class LicenseClientMixin(ClientRequestMixin):

    def Register(self, request:LicenseRegistrationRequest):
        """
            license 정보를 상태 정보 수정
        """
        ret = None
        license_status = None
        with self.get_command_center_channel() as channel:
            stub = rule_update_service_pb2_grpc.LicenseServiceStub(channel)
            retrying_stub_methods(stub)
            response_data = stub.Register(request, timeout=10)
            license_status = response_data.status

            if license_status == license_pb2.LicenseStatus.SITE_NONE:
                ret = "Site Code  Not Found [ {0} ]".format(request.site_code)
            elif license_status == license_pb2.LicenseStatus.CONFIRM:
                license_data = response_data.license_data
                """
                    license_data 처리.. 어디에 넣어야 하는가?
                    key 등록 - NBB 에서만 라이센스 등록
                """
                self._update_local(request.site_code)
            elif license_status == license_pb2.LicenseStatus.WAIT:
                ret = "Current Server Register [ {0} ]".format(request.site_code)
                """
                    최초 설치시에는 site_code 정보가 존재하지 않으므로 업데이트 해줘야함.
                    config 정보에 기본값은 '-' 이므로 재기동 하지 않으면 해당정보가 업데이트 안됨.
                """
                self._update_local(request.site_code)
            elif license_status == license_pb2.LicenseStatus.REJECT:
                ret = "Rejected Server Register [ {0} ]".format(response_data.approval_contents)
                self._update_local(request.site_code)

        return license_status, ret

    def Status(self):
        from command_center.library.AppConfig import gconfig
        ret = None
        license_status = None

        with self.get_command_center_channel() as channel:
            stub = rule_update_service_pb2_grpc.LicenseServiceStub(channel)
            retrying_stub_methods(stub)

            license_request_packet = license_pb2.LicenseRequest(hardware_uuid=gconfig.server_model.uuid,
                                                                machine_id=gconfig.server_model.machine_id)
            response_data = stub.Status(license_request_packet, timeout=10)
            license_status = response_data.status

            print(response_data.status)
            print(response_data.license_data)

            if license_status == license_pb2.LicenseStatus.CONFIRM:
                license_data = response_data.license_data
                """
                    받아오는것 정상 확인 되었다. license data 모델 테이블 수정되면 입력하면 됨.
                    nbb 는 해당 정보를 활용해서 file에 남기는 방식으로 진행 
                    relay 서버는 동기화
                """
                print(license_data)
                ret = ""
            elif license_status == license_pb2.LicenseStatus.WAIT:
                ret = ""
            elif license_status == license_pb2.LicenseStatus.REJECT:
                ret = "Rejected Server Register [ {0} ]".format(response_data.approval_contents)
        return license_status, ret

    def RegisterRelay(self, relayserver):
        with self.get_command_center_channel() as channel:
            stub = rule_update_service_pb2_grpc.LicenseServiceStub(channel)
            retrying_stub_methods(stub)

            response_data = stub.RegisterRelay(relayserver, timeout=10)
            license_status = response_data.status
            print(response_data.status)
            self._update_local(relayserver.site_code)

        return license_status

    def _update_local(self, site_code):
        print("UPDATE command_center_info SET site_code='{0}'".format(site_code))
        db.pmdatabase.execute("UPDATE command_center_info SET site_code='{0}'".format(site_code))
        gconfig.command_center.site_code = site_code
