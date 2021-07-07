"""
This script parses arguments for the CLI. The parser has been written
such that it can be easily expanded via the dict.
"""

import argparse
from config import config
from src.helpers import str2bool

DEFAULT_DICT = {
                'dataset_name': {
                    'default': config.DATASET_NAME,
                    'arg1': '-d',
                    'arg2': '--dataset_name',
                    'help': 'Specifiy which dataset to fetch from the cancer archive. \
                             This arg is used in following script: `tcia-api.py`',
                    'required': False,
                    'action': 'store',
                    'type': str},
                'workers': {
                    'default': config.WORKERS,
                    'arg1': '-w',
                    'arg2': '--workers',
                    'help': 'Set the maximum workers to use in the process. \
                             Its a good idea to test out which scale that fits your computer the best. \
                             This arg is used in following script: `tcia-api.py`',
                    'required': False,
                    'action': 'store',
                    'type': int},
                'thread_num': {
                    'default': config.THREAD_NUM,
                    'arg1': '-tn',
                    'arg2': '--thread_num',
                    'help': 'Specifiy how many concurrent processes to start at the same time. \
                             Its advisable to use a high number for large datasets. \
                             This arg is used in following script: `tcia-api.py`',
                    'required': False,
                    'action': 'store',
                    'type': int},
                 'use_cpu_count': {
                    'default': config.USE_CPU_COUNT,
                    'arg1': '-cpu_n',
                    'arg2': '--use_cpu_count',
                    'help': 'Set to true if all cores are to be used . \
                             This arg is used in following script: `tcia_api.py`',
                    'required': False,
                    'action': 'store_false',
                    'type': str2bool}
                    }

parser = argparse.ArgumentParser(description=__doc__)

for v in DEFAULT_DICT.values():
    parser.add_argument(
                v['arg1'],
                v['arg2'],
                help=v['help'],
                default=v['default'],
                required=v['required'],
                type=v['type']
                )

# Convert everythin to a dictionary
args = vars(parser.parse_args())
