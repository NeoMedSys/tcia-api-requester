# The Cancer Imaging Archive API Requester (alpha version)
[Not active]

The cancer imaging archive can provide some useful public datasets for experimenting with e.g. deep learning for medical diagnostics. The downside is that the data is hard to obtain if you are on a linux machine, which is why we have the tcia-api-requester. Use this wrapper to fetch any publically available dataset that includes the modalities MR, CT and PET. 


#### 00. Requirements
- linux
- poetry
- py39

#### 01. Getting started
1. Start by installing the dependencies from the toml file. Use poetry for this.

```
$ poetry install
```

2. Run the main python script (you might have to set the `PYTHONPATH`)

```
$ poetry run python api_request_controller.py
```

Use the command line arguments to request various datasets and to speed up the process

```
$ poetry run python api_request_controller.py -d <dataset-name> --use_cpu_count True --thread_num <n_threads> --workers <n_workers>
```

The maximum workers will be set to the number of cores times the user specified amount of workers if the use_cpu_count flag is true. 


3. Data will be stored in the following order:
```
patient_uid
   study_uid
       series_uid
           series_description_uid
                image.dcm
```
