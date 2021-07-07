"""
This script contains helper functions for the TAr api requester.
"""
# externals
import os
from tqdm.contrib import tzip
from tqdm import tqdm
from zipfile import ZipFile
# internals
from config import config
from config.logger import log
from src.helpers import api_request, check_make_folder, timer


@timer
def get_series_list(dataset_name: str) -> dict:
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
    dict
        A nested dict containing information about the series uuids.
    str
        A string value for the name of the dataset
    """
    # update the patient parameter dict
    config.get_patient_params.update({'Collection': dataset_name})

    # who you gonna call
    resp = api_request(
                            url=config.URL_PATIENT,
                            params=config.get_patient_params,
                            is_series=False
                            )

    patients = resp.json()
    if patients:
        for idx in tqdm(range(len(patients)), total=len(patients)):
            patient = patients[idx].get('PatientID')
            # update the series params with patient
            config.get_series_params.update({
                                            'PatientID': patient,
                                            'Collection': dataset_name
                                            })

            # I said, who you gonna call
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
                        # series_dict.update({patient: {}})
                        # series_dict[patient].update({uid_tag: []})
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

    # Create the folder for the dataset
    check_make_folder(folder=DATA_PATH, verbose=True)

    return DATA_PATH, config.series_instances_dict


@timer
def get_instance_series(
                siuid_list: list,
                stuid_list: list,
                sidesc_list: list,
                patient: str,
                data_path: str
                ):
    """This is a helper function that uses the infomation about the series UUIDs to extract the acutal dicom files. The dicom
    files will be placed on a specific disk-place in specific hierarchy which is also needed by the
    NIFTI database.
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
    data_path : str
        Specify the `data_path` to where you want the data to be placed.
    Returns
    -------
    None
    """
    # define a mutable dict
    get_instance_params = {'SeriesInstanceUID': 'placeholder'}
    # make sure the patient string is clean
    patient = patient.replace(' ', '-').lower()
    # Now make an API request for each SeriesInstance
    for siUID, stUID, sdUID in tzip(siuid_list[0], stuid_list[0], sidesc_list[0]):

        # update the SeriesInstanceUID parameter
        get_instance_params.update({'SeriesInstanceUID': f'{siUID}'})

        resp = api_request(
                        config.URL_IMG,
                        params=get_instance_params,
                        is_series=False
                        )

        # define the stringnames for the folders and filepaths
        study = f'{stUID[-10:]}'
        series = f'{siUID[-10:]}'
        # check if file is something else than zip
        filename = f'uid{siUID[-9:]}.zip'
        assert filename.endswith('.zip')

        # clean dem strings
        patient = patient.translate({ord(char): None for char in config.CHAR_TO_REMOVE})
        sdUID = sdUID.translate({ord(char): None for char in config.CHAR_TO_REMOVE})
        sdUID = sdUID.replace(' ', '-').lower()

        # create a folder for the StudyInstance and SeriesInstance
        patient_folder = os.path.join(data_path, 'patient-{patient}').format(patient=patient)
        study_folder = os.path.join(patient_folder, 'study-{study}').format(study=study)
        series_folder = os.path.join(study_folder, 'series-{series}').format(series=series)
        sedesc_folder = os.path.join(series_folder, 'sedesc-{sedesc}').format(sedesc=sdUID)

        if patient_folder.islower():
            check_make_folder(patient_folder)
        else:
            log.error(f'found upper case values in {patient_folder}')
        check_make_folder(study_folder)
        check_make_folder(sedesc_folder)

        # If payloads come in different sizes then the chunk_size must adapt to it
        chunk_size = config.MEGABYTE if len(resp.content) > config.MEGABYTE else 100

        # download the zip files in the instance folder
        filepath = os.path.join(sedesc_folder, '{filename}')
        with open(filepath.format(filename=filename), 'wb') as fp:
            try:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    fp.write(chunk)
            except IOError:
                log.error(f'writing chunk: {chunk} to folder failed', exc_info=True)

        try:
            # Extract the zip file and delete it thereafter
            for item in os.listdir(sedesc_folder):
                if item.endswith('.zip'):
                    ZipFile(filepath.format(filename=item)).extractall(sedesc_folder)
                    os.remove(os.path.join(sedesc_folder, item))
        except Exception:
            log.error(f'zipefile extraction failed for {item}', exc_info=True)
