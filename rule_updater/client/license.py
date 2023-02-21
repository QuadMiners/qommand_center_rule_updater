import logging
import time

from library.database.fquery import fetchone_query_to_dict
from library.rpc.retry import retrying_stub_methods
from protocol import rule_update_service_pb2_grpc
from protocol.license import license_pb2
from protocol.site import site_pb2
from rule_updater import ResponseRequestMixin

logger = logging.getLogger(__name__)


class LicenseClientMixin(ResponseRequestMixin):

    def Register(self):
        channel = self.get_update_server_channel()
        stub = rule_update_service_pb2_grpc.LicenseServiceStub(channel)
        retrying_stub_methods(stub)

        license_regist_request_packet = license_pb2.LicenseRegistrationRequest()
        license_regist_request_packet.reg_user_name = "aaa"
        license_regist_request_packet.reg_user_tel = "010-0000-0000"
        license_regist_request_packet.server_type = "relay"
        license_regist_request_packet.hardware_uuid = "0000-0000-0000-0000"
        license_regist_request_packet.machine_uuid = "aaaa-bbbb-cccc-dddd"

        response_data = stub.Register(license_regist_request_packet, timeout=10)
        license_status = response_data.status

        if license_status == license_pb2.LicenseStatus.APPROVE:
            license_data = response_data.license_data
            """
                license_data 처리.. 어디에 넣어야 하는가?
            """
        else:
            pass

    def Status(self):
        channel = self.get_update_server_channel()
        stub = rule_update_service_pb2_grpc.LicenseServiceStub(channel)
        retrying_stub_methods(stub)

        license_request_packet = license_pb2.LicenseRequest()
        license_request_packet.hardware_uuid = "0000-0000-0000-0000"
        license_request_packet.machine_id = "aaaa-bbbb-cccc-dddd"

        response_data = stub.Status(license_request_packet, timeout=10)
        license_status = response_data.status

        if license_status == license_pb2.LicenseStatus.APPROVE:
            license_data = response_data.license_data
            """
                license_data 처리.. 어디에 넣어야 하는가?
            """
        else:
            pass








