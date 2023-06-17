"""
This script contains helper functions for the TAr api requester.
"""
# externals
import os
import sys
from tqdm.contrib import tzip
from tqdm import tqdm
from zipfile import ZipFile, BadZipFile, LargeZipFile
from typing import Dict, Union, NoReturn, List
# internals
from config import config
from config.logger import log
from src.helpers import api_request, check_make_folder, timer


@timer
def get_series_list(dataset_name: str) -> Union[os.PathLike, Dict[str, str]]:
    """Extract all the information about a series UUID in a specific dataset that lies
    in the cancer imaging archive. The extractions are done over API requests. The information
    from all the series UUIDs in the given dataset will extracted and placed in dict for subsequent
    requests.
    Parameters
    ----------
    dataset_name : str
        Specify which dataset to extract info for the series UUIDS from.
    Returns
    -------
    Dict[str, str]
        A nested dict containing information about the series uuids.
    str
        A string value for the name of the dataset
    """
    try:
        # update the patient parameter dict
        config.get_patient_params.update({'Collection': dataset_name})

        # who you gonna call
        resp = api_request(
                        url=config.URL_PATIENT,
                        params=config.get_patient_params,
                        is_series=False
                        )

        patients = resp.json()
    except ValueError:
        log.error(
                f'I tried request the patient list for the dataset {dataset_name}, but received ({resp.text}) with status {resp.status_code} and URL {resp.url}',
                exc_info=True
                )
        sys.exit(1)

    if patients:
        for idx in tqdm(range(len(patients)), total=len(patients)):
            patient = patients[idx].get('PatientId')
            # update the series params with patient
            config.get_series_params.update({
                                            'PatientID': patient,
                                            'Collection': dataset_name
                                            })

            # who you gonna call
            series, collection = api_request(
                                    url=config.URL_SERIES,
                                    params=config.get_series_params
                                    )
            # NOTE: not sure if this suitable for concurrency (yet)
            for idx, intances in enumerate(range(len(series))):
                for uid_tag in config.SERIES_INSTANCES_LIST:
                    uid = series[intances].get(uid_tag)
                    uid = 'missing' if uid is None else uid
                    if idx < 1:
                        config.series_instances_dict[patient][uid_tag] = []
                        config.series_instances_dict[patient][uid_tag].append(uid)
                    else:
                        config.series_instances_dict[patient][uid_tag].append(uid)
    else:
        log.error(f'response is empty, check if the dataset {dataset_name} limited or if patientID is listed', exc_info=True)
        raise ValueError('can only process data that contains patientID')

    # set some constants
    DATASETNAME = dataset_name.replace(" ", "-").lower()
    DATA_PATH = config.DCM_RAW_DATASET_PATH.format(collection=DATASETNAME)

    return DATA_PATH, config.series_instances_dict


@timer
def get_instance_series(
                siuid_list: List[str],
                stuid_list: List[str],
                sidesc_list: List[str],
                patient: str,
                data_path: os.PathLike
                ) -> NoReturn:
    """This is a helper function that uses the infomation about the series UUIDs to extract the acutal dicom files. The dicom
    files will be placed on the local storage in a specific hierarchy.
    Parameters
    ----------
    siuid_list : list
        The `siuid_list` contains the SeriesUUIDs.
    stuid_list : list
        The `stuid_list` contains the StudyUUIDs.
    sidesc_list : list
        The `sidesc_list` conatains the SeriesDescriptionUUIDS.
    patient : str
        The `patient` string indicates which patient in the dataset to extract dicom
        files for.
    data_path : os.PathLike
        Specify the `data_path` to where you want the data to be placed.
    Returns
    -------
    NoReturn
    """
    # define a mutable dict
    # get_instance_params = {'SeriesInstanceUID': 'placeholder'}
    # make sure the patient string is clean
    patient = patient.replace(' ', '-').lower()
    # Now make an API request for each SeriesInstance
    for siUID, stUID, sdUID in tzip(siuid_list[0], stuid_list[0], sidesc_list[0]):

        # update the SeriesInstanceUID parameter
        # get_instance_params.update({'SeriesInstanceUID': f'{siUID}'})

        resp = api_request(
                        config.URL_IMG,
                        params={'SeriesInstanceUID': siUID},
                        is_series=False
                        )

        # define the stringnames for the folders and filepaths
        study = f'{stUID[-10:]}'
        series = f'{siUID[-10:]}'
        # check if file is something else than zip
        filename = f'uid{siUID[-9:]}.zip'
        if not filename.endswith('.zip'):
            raise ValueError(f'The filename {filename} is not a valid zipfile')

        # clean dem strings
        patient = patient.translate({ord(char): None for char in config.CHAR_TO_REMOVE})
        sdUID = sdUID.translate({ord(char): None for char in config.CHAR_TO_REMOVE})
        sdUID = sdUID.replace(' ', '-').lower()

        # create a folder for the StudyInstance and SeriesInstance
        patient_folder = os.path.join(data_path, 'patient-{patient}').format(patient=patient)
        study_folder = os.path.join(patient_folder, 'study-{study}').format(study=study)
        series_folder = os.path.join(study_folder, 'series-{series}').format(series=series)
        sedesc_folder = os.path.join(series_folder, 'sedesc-{sedesc}').format(sedesc=sdUID)

        check_make_folder(patient_folder)
        check_make_folder(study_folder)
        check_make_folder(sedesc_folder)

        # If payloads come in different sizes then the chunk_size must adapt to it
        chunk_size: int = config.MEGABYTE if len(resp.content) > config.MEGABYTE else 100

        # download the zip files in the instance folder
        filepath: os.PathLike = os.path.join(sedesc_folder, '{filename}')
        with open(filepath.format(filename=filename), 'wb') as fp:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                try:
                    fp.write(chunk)
                except IOError:
                    log.error(f'writing chunk: {chunk} to folder failed', exc_info=True)

        # Extract the zip file and delete it thereafter
        for item in os.listdir(sedesc_folder):
            if item.endswith('.zip'):
                try:
                    ZipFile(filepath.format(filename=item)).extractall(sedesc_folder)
                    os.remove(os.path.join(sedesc_folder, item))
                except (BadZipFile, LargeZipFile, ValueError):
                    log.error(f'zipefile extraction failed for {item}', exc_info=True)
