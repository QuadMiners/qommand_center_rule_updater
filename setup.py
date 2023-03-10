import os
import subprocess
import sys
from distutils.command.clean import clean as _clean
from distutils.debug import DEBUG

from setuptools import setup

PROTO_FILES = [
    'protocol/rule_update_service.proto',
    'protocol/heartbeat/heartbeat_packet.proto',
    'protocol/version/version_type.proto',
    'protocol/version/version_download_packet.proto',
    'protocol/version/version_check_packet.proto',
]

def generate_proto(source):
    """Invoke Protocol Compiler to generate python from given source .proto."""

    if not os.path.exists(source):
        sys.stderr.write('Can\'t find required file: %s\n' % source)
        sys.exit(1)

    output = source.replace('.proto', '_pb2.py')
    if (not os.path.exists(output) or
            (os.path.getmtime(source) > os.path.getmtime(output))):
        if DEBUG:
            print('Generating %s' % output)
        " python -m grpc.tools.protoc -I/usr/local/include -I. --python_out=./ --grpc_python_out=./ ./protocol/*.proto "
        protoc_command = ['python', '-m', 'grpc.tools.protoc', '-I.', '-I/usr/local/include/', '--python_out=./', '--grpc_python_out=./', source]
        if subprocess.call(protoc_command) != 0:
            sys.exit(1)


class clean(_clean):
    def run(self):
        # Delete generated files in the code tree.
        for (dirpath, dirnames, filenames) in os.walk("."):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if filepath.find("proto") and (filepath.endswith("_pb2.py") or filepath.endswith("_pb2_grpc.py")):
                    os.remove(filepath)
        # _clean is an old-style class, so super() doesn't work.
        _clean.run(self)

class build_py(object):

    def run(self):
        for proto in PROTO_FILES:
            generate_proto(proto)


#clean().run()

build_py().run()

setup(
    cmdclass={
        'clean': clean,
        #'build_py': build_py,
    },
)