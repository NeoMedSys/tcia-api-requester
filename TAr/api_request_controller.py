"""
This script runs an API request to the cancer imaging archive and returns data
in strutured file system corresponding to the DICOM hierarchy:
--> Dataset
    --> patientID
        --> ExamUID
            --> SeriesInstanceUID
                --> DICOM-Series
Author: Jon E Nesvold
"""
# internals
from config import arg_parser
from src.helpers import get_partition_idx, check_make_folder
from src.tcia_api import get_series_list, get_instance_series
from config.logger import log
# externals
from typing import List, NoReturn
import concurrent.futures as cf
from multiprocessing import cpu_count
from dataclasses import dataclass


@dataclass
class RequestController:
    """This a request controller that integrates all the modules to make the
    TAr work. The run method ties all the steps together in the end.
    Attributes
    ----------
    dataset_name : str
        Let the process know which dataset to use via `dataset_name`.
    workers : int
        Set the number of `workers` to use in the concurrency.
    thread_num : int
        Set the number threads to use in the concurrency.
    use_cpu_count : bool
        Set `use_cpu_count` to true if you want to scale up the amount of worker with
        the CPU core count.
    """
    dataset_name: str = arg_parser.args['dataset_name']
    workers: int = arg_parser.args['workers']
    thread_num: int = arg_parser.args['thread_num']
    use_cpu_count: int = arg_parser.args['use_cpu_count']

    def fetch_series(self) -> NoReturn:
        """
        This method controls the series list request
        """
        self.data_path, self.patient_dict = get_series_list(self.dataset_name)

        # Create the folder for the dataset
        check_make_folder(folder=self.data_path, verbose=True)

        if len(self.patient_dict) > 50:
            log.warning('There are more than 50 patients in this dataset')

        log.info(f'the dataset will be stored here: {self.data_path}')

    def fetch_instances(self) -> NoReturn:
        """
        This method controls the influx of intances from the dataset
        """
        UID_LIST = []
        max_workers: int = cpu_count() * self.workers if self.use_cpu_count else self.workers
        # NOTE: if keeps staying flaky, try executor.submit with a list comprehension
        with cf.ThreadPoolExecutor(
                            max_workers=max_workers,
                            thread_name_prefix='tcia_api'
                            ) as executor:
            for patient, patient_info in self.patient_dict.items():
                sedecs_list: List[str] = get_partition_idx(
                                        full_list=patient_info.get('SeriesDescription'),
                                        thread_num=self.thread_num
                                        )
                study_list: List[str] = get_partition_idx(
                                        full_list=patient_info.get('StudyInstanceUID'),
                                        thread_num=self.thread_num
                                        )
                series_list: List[str] = get_partition_idx(
                                        full_list=patient_info.get('SeriesInstanceUID'),
                                        thread_num=self.thread_num
                                        )
                UID_LIST.append(tuple((
                                            series_list, study_list,
                                            sedecs_list, patient,
                                            self.data_path
                                            )))
                executor.map(lambda p: get_instance_series(*p), UID_LIST)

    def run(self) -> NoReturn:
        log.pipe(f"""
                ###############################################
                ## Running the API requester with the following
                ###############################################
                Dataset name: {self.dataset_name}
                Workers: {self.workers}
                Concurrent Threads: {self.thread_num}
                Using CPU core count: {self.use_cpu_count}
                Note!
                if Using CPU cores is True then:
                    max_workers = {self.workers * cpu_count()}
                if not:
                    max_workers = {self.workers}
                TCIA-API-Requester 0.1.0-beta1
                """)
        log.info('Fetching series')
        self.fetch_series()
        log.info('Fetching instances')
        self.fetch_instances()
        log.pipe('Data extracted and saved, you are all set (⌐■_■)')


if __name__ == '__main__':
    RequestController().run()
