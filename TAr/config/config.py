"""
This is the configuration file for the whole project. It contains
configurable variables, environment variables and constants that
are used in various modules, classes and controllers.
"""

# externals
import os
from fake_useragent import UserAgent
# internals
from src.helpers import nested_dict


# paths
ROOT = os.getcwd()
RAW_DATA = os.path.join(ROOT, 'data/raw')
PREPROC_DATA = os.path.join(ROOT, 'data/processed')
PREPROC_TESTING_DATA = os.path.join(ROOT, 'nifti_database/data/processed')

# path used in the controllers
DCM_RAW_DATASET_PATH = os.path.join(RAW_DATA, 'raw-{collection}-dicom')
NII_RAW_DATASET_PATH = os.path.join(RAW_DATA, 'raw-{collection}-nifti')
NII_PREPROC_DATASET_PATH = os.path.join(PREPROC_DATA, 'preproc-{collection}-nifti')
JSON_FILE_PATH = os.path.join(RAW_DATA, 'json_files')
NII_JSON_PATH = os.path.join(JSON_FILE_PATH, 'nifti_{project_name}.json')
HEADER_JSON_PATH = os.path.join(JSON_FILE_PATH, 'header_{project_name}.json')

# config for the TCIA API requests
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# URLs
BASE_URL = 'https://services.cancerimagingarchive.net/nbia-api/services/v1'
RESOURCE = 'TCIA'
QUERY_IMGS = 'getImage'
QUERY_SERIES = 'getSeries'
QUERY_PATIENT = 'getPatient'

# The final base URLs
URL_SERIES = os.path.join(BASE_URL, QUERY_SERIES)
URL_PATIENT = os.path.join(BASE_URL, QUERY_PATIENT)
URL_IMG = os.path.join(BASE_URL, QUERY_IMGS)

# Some variables for extension checks
imgs_with_ext = 0
imgs_without_ext = 0
non_imgs = 0

# Default params for the TAr
DATASET_NAME = 'Brain-Tumor-Progression'
WORKERS = 5
THREAD_NUM = 5
USE_CPU_COUNT = False

CHAR_TO_REMOVE = ['#', '%', '-', '*', '@', '!']

# Parameters for to use in the base URL
get_patient_params = {
                    'format': 'json',
                    'Collection': 'placeholder'
                    }
get_series_params = {
                    'format': 'json',
                    'Collection': 'placeholder',
                    'PatientID': 'placeholder'
                    }

USER_AGENT = UserAgent().chrome
# List used in the data handling
series_instances_dict = nested_dict()
SERIES_INSTANCES_LIST = ['SeriesInstanceUID', 'StudyInstanceUID', 'SeriesDescription']
CONVERSION_ITEMS = ['img_array', 'patientID', 'StudyInstanceUID', 'SeriesInstanceUID', 'SeriesDescription']
conversion_info = nested_dict()

MEGABYTE = 1024 * 1024
