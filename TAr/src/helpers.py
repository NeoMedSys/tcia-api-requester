
# externals
import re
import os
import requests
from requests.exceptions import HTTPError
from time import time
from timeit import default_timer
from functools import wraps
import argparse
from collections import defaultdict
# internals
from config.logger import log
from config import config

START_TIME = default_timer()


def str_has_digit(input_string: str) -> bool:
    """Check if a string has digits in it.
    Parameters
    ----------
    input_string : str
        your `input_string` that you want to inspect.
    Returns
    -------
    bool
        True if there is digit in the string, false otherwise.
    """
    return any(char.isdigit() for char in input_string)


def str_has_letters(input_string: str) -> str:
    """Check if there are letters in the string.
    Parameters
    ----------
    input_string : str
        The `input_string` to inspect.
    Returns
    -------
    str
        The letters present are returned.
    """
    return re.search('[a-zA-Z]', input_string)


def check_make_folder(folder: str, verbose: bool = False):
    """Check if a folder exsists and if not make it.
    Parameters
    ----------
    folder : str
        Give path to the `folder`.
    verbose : bool
        Set to true if `verbose` is necessary.
    Returns
    -------
    type
        Nothin is returned.
    """
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
            if verbose:
                print(f'did not find the folder, making base folder: {folder}')
    except OSError:
        log.error(f'was not able to create {folder}', exc_info=True)


def timer(orig_func):
    """This is custom timer decorator.
    Parameters
    ----------
    orig_func : object
        The `orig_func` is the python function which is decorated.
    Returns
    -------
    type
        elapsed runtime for the function.
    """
    @wraps(orig_func)
    def wrapper(*args, **kwargs):
        t1 = time()
        result = orig_func(*args, **kwargs)
        t2 = time() - t1
        print('Runtime for {}: {} sec'.format(orig_func.__name__, t2))
        return result
    return wrapper


def api_request(url: str, params: dict, is_series: bool = True):
    """This is wrapper function for sending a simple request without opening a session.
    Parameters
    ----------
    url : str
        its the base `url` for where the request is sent.
    params : dict
        Additoinal parameters to send with the base URL.
    is_series : bool
        If the fucntion is used for a series call, then set `is_series` True such that json is returned.
    Returns
    -------
    resp Object
        the http response from the request is returned. The resp can either be a Zipfle or json
        depending on the whether it is from a instance call or series call respectivley.
    collection str
        The dataset name
    """
    headers = {'User-Agent': config.USER_AGENT}
    try:
        resp = requests.get(url, params=params, verify=True, headers=headers)
    except HTTPError as e:
        log.error(
            f'request failed, this is the url: {resp.request.url}',
            exc_info=True
            )
        if resp.status_code != 200:
            raise e(f'request failed with status code: {resp}')
        if resp.status_code == 204:
            raise e(f'request failed with status code: {resp}')

    if is_series:
        return resp.json(), params.get('Collection').lower()
    else:
        return resp

# def api_request_scans(
#             datapath: str,
#             url: str, siUID: str, session
#             ):

#     with session.get(url, siUID) as response:
#         if response.status_code == 200:
#             print('connection established')
#         else:
#             raise HTTPError(f'request failed with status code: {response.status_code}')
#             print(f'the url: {response.requests.url}')

#     elapsed = default_timer() - START_TIME
#     time = f'{elapsed}s'
#     print("{0:<30} {1:>20}".format(siUID, time))

#     return response.iter_content(chunk_size=100)


# async def asynchronous_data_extraction(serieslist: list):
#     print('{0:<30} {1:>20}'.format('ZipFile', 'Download complete:'))
#     with ThreadPoolExecutor(max_workers=10) as executor:
#         with requests.Session() as session:
#             loop = asyncio.get_event_loop()
#             START_TIME = default_timer()
#             tasks = [
#                 loop.run_in_executor(
#                     executor,
#                     api_request_scans,
#                     *(session, siUID)
#                 ) for siUID in serieslist]

#             for response in await asyncio.gather(*tasks):
#                 pass


def get_partition_idx(full_list: list, thread_num: int):
    """This function partitions a list into smaller sized lists which are then appended to
    a final list. The lenght of the partition lists depends on the full list length and the
    amount threads the user wants to run when applying the function in `TAr`.
    Parameters
    ----------
    full_list : list
        This is the original list `full_list`.
    thread_num : int
        Use `thread_num` to specify how many partitions to make from the original list.
    Returns
    -------
    type list
        Partioned list.
    """
    # Find the length of the full list_input
    list_len = len(full_list)
    if list_len == 1:
        log.warning('f the following full list has only length 1 {full_list}')
        thread_num = 1
    assert list_len >= thread_num, f'the number of threads: {thread_num} exceeds the length of the full list: {list_len}'

    # Set the length for the partioned lists
    partion_list_length = list_len // thread_num
    # Get the modulus from the division
    partition_modulus = len(full_list) % thread_num

    # Set som variables for the loop
    partition_idx_list = []
    list_len_threshold = list_len
    idx1 = 0
    idx2 = partion_list_length
    try:
        # append the partitions to a list and increment until
        # the criterion is reach
        while partion_list_length < list_len_threshold:
            partition_idx_list.append(full_list[idx1:idx2])
            idx1 += partion_list_length
            idx2 += partion_list_length
            list_len_threshold -= (partion_list_length + partition_modulus)
        else:
            # Include the very last partition, which can vary in size from the
            # rest pf the partitions
            idx3 = list_len-(partion_list_length + partition_modulus)
            partition_idx_list.append(full_list[:-idx3])
    except ValueError:
        log.error(f'while loop failed at {idx1}:{idx2}', exc_info=True)
    return partition_idx_list


def str2bool(v):
    """
    Converts the string values in the argparse to booleans
    """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def nested_dict():
    """Reacursive dict function for making nested dicts.
    """
    return defaultdict(nested_dict)


def iter_row(cursor, size: int):
    while True:
        rows = cursor.fetchmany(size)
        if not rows:
            break
        for row in rows:
            yield row

