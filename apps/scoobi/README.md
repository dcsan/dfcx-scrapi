## setup

create a virtual env and install required packages:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Credentials

Download a service account JSON credentials file from GCP and move it to:
 `config/CLIENTB-dev-creds.json`


## Config file

So we know where everything lives, we put info into a config file.

I'm using a python file so we can get type checking on this.

[config/client_config.py](config/client_config.py)

Based on what you're working on, you'll need to change some of those settings.

## Install

If you're working on a new project, the first time you run you'll need to install the database tables.

The schemas are in data/schemas and you can setup with `Installer.create_tables(config)`
get the config from step above.

You will only have to do this once, or if you modify the schema.


## Data pipeline

If you need to export data from another warehouse, here's a simple query

```sql
SELECT
  max(current_sprint_number)
FROM DATASET_NAME.feedback_annotations
where
dataset_display_name LIKE '%CLIENTB CHANNEL%'
```

```sql
SELECT
  *
FROM DATASET_NAME.feedback_annotations
where
  current_sprint_number=26

AND
  dataset_display_name LIKE '%CLIENTB CHANNEL%'

order by
  session_id, position
```
(change the sprint number from 26 to whatever is latest)

place it in `data/ignored/sp-xx-channel.csv` (so it doesn't get accidentally committed to git)

## Ingesting data

If you're running this whole setup locally, eg from a command line, then use the `cli.py` file

You can edit that to change settings, eg point to the right file name and set_name

    fname = 'CLIENTB/sp26-voice.csv'
    set_name = 'sp26-CLIENTB-voice'




## Makefile
Many key tasks are contained in the [Makefile](Makefile).
This is like an old unix way to keep a list of shortcuts.
So you can just type `make $taskname` or even just `make` to run the default first task.
These commands give you tab-completion.


## Tests

** IN PROGRESS **

Then run the basic connection test with `pytest`.
You should see something like this:

```
(venv) $ pytest
=========================== test session starts ============================
platform linux -- Python 3.9.2, pytest-6.2.5, py-1.10.0, pluggy-1.0.0
rootdir: /usr/local/path/to/user/scoobi, configfile: pytest.ini, testpaths: ./test
collected 2 items

test/test_setup.py::test_creds PASSED                                [ 50%]
test/test_setup.py::test_db_access PASSED                            [100%]

============================ 2 passed in 1.73s =============================
(venv) dcollier@dcsan:~/dev/fbl/scoobi$
```

You can customize which database tables and other defaults are tested in the [./lib/configlib.py](./lib/configlib.py)
