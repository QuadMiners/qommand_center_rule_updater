from functools import lru_cache
import platform
import subprocess

from termcolor import cprint, colored

from command_center.client.license import LicenseClientMixin
from command_center.command import print_help_msg, ToolCommandMixin, ValueInput
from command_center.protocol.license import license_pb2
from command_center.protocol.site import server_pb2
from command_center.library.AppConfig import gconfig
from command_center.command.command import hostname


class LicenseCommand(LicenseClientMixin,ToolCommandMixin):
    intro = colored('License Command.\nType help or ? to list commands.\n', 'yellow')
    prompt = colored('%s ( license )# ' % hostname, 'cyan')

    def help_registry(self):
        print_help_msg("Show Memory Status of the Current Process",
                       usage=["(license)# registry"])

    def do_registry(self, args):
        """
            hardware_uuid = models.CharField(max_length=256, verbose_name="UUID")
    machine_id = models.CharField(max_length=256, verbose_name="Machine ID 정보")
    site_code = models.CharField(max_length=64, verbose_name="Site Code")
    manufacturer = models.CharField(max_length=64, verbose_name="제조업체")
    product_name = models.CharField(max_length=256, verbose_name="제품명")
    serial_number = models.CharField(max_length=256, verbose_name="Serial")

        """
        site_code = None
        serial_number = ''
        site_code = ValueInput("Site Code : ")
        serial_number = ValueInput("Serial Number: ")
        server = server_pb2.RelayServer(hardware_uuid=gconfig.server_model.uuid,
                                        machine_id=gconfig.server_model.machine_id,
                                        site_code=site_code,
                                        manufacturer=gconfig.server_model.manufacturer,
                                        product_name=gconfig.server_model.product_name,
                                        serial_number=serial_number)

        equest_packet = self.RegisterRelay(server)
