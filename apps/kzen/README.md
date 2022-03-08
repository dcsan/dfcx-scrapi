# KZEN
A suite of tools for different phases of the conversation workflow.


# cx_testrunner

A way to run tests against CX agents using the API and a simple DSL for describing the tests.

See the [Makefile](Makefile) for various tasks to help with running this service.

I recommend making a `dev` dir in your home directory to put all this into.

## setup / install Python Virtual Env

python-setup:

	# these commands have to be run with sudo in the current shell
	sudo apt-get install python3-venv
	python3 -m venv venv
	source venv/bin/activate
	pip3 install --upgrade pip
	python3 -m pip install --upgrade setuptools

- All the python modules

    cd ../cx_testrunner
    pip install -r requirements.txt

Now you should have a functional virtualenv. Make sure to activate it before
starting work each day:

    . venv/bin/activate.sh


## Google Cloud Credentials (IAM file)

Go to GCP dashboard and download a json credentials file for your project.

After downloading from GCP dashboard rename the downloaded .json keys as `default-iam-creds.json` and move to the `config` directory.
eg

    cp ~/Downloads/gcp-proj-1234567.json config/default-iam-creds.json


## SCRAPI Library

We're now using this from PIP package, so no longer needed to use a git submodule.

If you do also want to extend scrapi, checkout a copy in the directory *above* this project and run:

`make local-scrapi`

this basically just runs:
`pip install ../python-dialogflow-cx-high-level-api`


## Setup App Config

There are a bunch of credentials needed.
After the 'git clone' you will have the credentials in the config directory.
So now, you need to duplicate the `app_config.json.example` file:

        cp config/app_config.json.example config/app_config.json

And then edit the new app_config.json to replace with your apps info.
eg you'll have to replace these fields:

```json
{
    "COMMENT": "the bootstrap config sheet",
    "KZEN_CONFIG_DOC": "GOOGLE-DOC-ID",
    "DEFAULT_CREDS_PATH": "./config/default-iam-creds.json",
    "BQ_PROJECT": "big-query-xxx",
    "BQ_DATASET": "bq-bqdataset-xx",
    "BQ_RUNS_TABLE_NAME": "runs",
    "FLOWSTATS_TABLE": "bqdataset-xx.flowstats",
    "RUNS_TABLE": "bqproj.bqdataset.runs",
    "DASHBOARD_URL": "https://datastudio.google.com/c/reporting/DASHURL/page/",

    "BQ_TABLES": [
        "agents",
        "flowstats",
        "gdocs",
        "intents",
        "runs",
        "sandbox",
        "stats",
        "test_runs",
        "test_sets"
    ]
}
```

details:

```
    - "KZEN_CONFIG_DOC": "1gtWBzUFT_u8uOjE58qKQFXdh97TRfqRMpiEk0k8smxE",
    # the main google doc with agents, gdocs etc

    "DEFAULT_CREDS_PATH": "./config/default-iam-creds.json",
    # where your IAM creds file lives

    "BQ_PROJECT": "YOUR_GCP_PROJECT",
    # bigquery project

    "BQ_DATASET": "YOUR-BQ-DATASET",
    # dataset

    "BQ_RUNS_TABLE_NAME": "runs",
    # table for keeping results of benchmark runs

    "FLOWSTATS_TABLE": "YOUR-BQ-DATASET.flowstats",
    # stats

    "RUNS_TABLE": "`YOUR_GCP_PROJECT.YOUR-BQ-DATASET.runs`",
    # BM runs - yes this duplicates the above!

    "DASHBOARD_URL": "https://datastudio.google.com/c/reporting/03b29665-43e5-47d3-afa6-e0ab1c1c023d/page/qGJ0B",
    # where you can view results

    # and a list of tables used in various places in the project
    "BQ_TABLES": [
        "agents",
        "flowstats",
        "gdocs",
        "intents",
        "runs",
        "sandbox",
        "stats",
        "test_runs",
        "test_sets"
    ]

```

### KZEN config doc

The kzen config doc is the kind of "master" bootstrap doc that says where everything else lives.

We "bootstrap" the system from a google sheet, ie telling it where it can find agents to work and other google docs that contain tests or sets of utterances. From then on inside the app we just refer to those agents etc by their name.

You need two tabs for "agents" and "docs"
You might not need all of these filled out, eg docs is really just for the benchmarking tool, not needed for tests.

TODO:
write up in more detail the tabs and fields there.

You can find out more about sharing google docs in the documentation for the gspread package we use.

## DataBase

We use google bigquery to store data.

There are schema dumps in [config/schema](config/schema)

eg for the benchmarky results are stored in
[config/schema/runs.txt](config/schema/runs.txt)

There is no automated script to apply the schemas, so you'll need to use the bigquery web UI.

I think the first time you write data, it may create the schema for you, but this is sometimes unreliable as types are guessed. eg a string for a boolean might result.

If you modify the schema in the webUI you can update the dumps by calling `biglib.dump_all_schemas()`

## Data Structures
These are the minimum fields needed by the DB tables. similar to the data in the config sheet

router
- agents:
  - cname
  - notes
  - gcp_env
  - agent_url
  - creds_path
  - agent_path (seems needed now?)

- gdocs:
  - cname
  - tabname
  - url
  - sheet_id

  - usecase
  - type
  - notes


## Test running locally

eg to run a single test run of a tab of the test run google doc.

edit the `runner.py` and check under main there's something like this:

```python
def main():
    '''lets do it'''
    configlib.fetch_all_configs()
    testone('AMNT-chat') # one named tab
```

explanation:
`fetch_all_configs` will read the kzen config doc to get names for all agents and other bootstreap data, and store in the BQ tables for agents and gdocs.

`testone('AMNT-chat')` will load the set of tests on the testsheet, for the tab 'AMNT-chat' and run those tests.

so to execute this, after setting up your *Virtual Env* (see above) you can type:

    python runner.py


and you should see something [like this output](docs/testrun.txt).

This 'runner' file is kind of a scratchpad for when you're working as a single dev and just want to remember what commands to run, what params they take etc. You'll see a bunch of helper functions sitting here.

For example:

`bench_run('dc-AGENT-ID-TR', 'BILL-coreset')`

will run benchmarky with the agent and testset listed.

The methods in runner like `bench_run` are also called by the front-end app passing parameters that the user chooses. The `runner` file is just a quick way to run things from the command line without having to use a mouse (!) and boot up the UI. Also to test things.


## Running Client and server apps

If you want to see the front-end of the app running locally

To start server AND client apps:
in one shell

    make server

in another shell:

    cd client
    make

Then open at top left the web preview, a URL something like

https://xxxxxx.cs-us-west1-olvl.cloudshell.dev/kzen/testrunner

You should be able to now operate the App!


## Tracing a full event cycle

### Server
Main entry point when running locally is in `runner.py` eg when just want to run a single script I edit this file and do

    python runner.py

Server routing is in `main.py` - which is the file app engine runs on startup. So the sequence might be:


- Front end calls an api like `/api/testone`

- this route is defined in `main.py` which reads passed in params and calls the method in `runner`

```python
@app.route('/api/testone')
def testone():
    ...
    result = runner.testone(tabname)
```

- runner.py
will kind of dispatch that method to the right piece of core code inside the app, in this case an instance of TestRunner()

```
def testone(tabname):
    ...
    tester = TestRunner()
    results = tester.run_one_tab(tabname)
    return { ...
        'results': results
    }

```

### Client

Is a small react app, the pages are in [client/src/pages](client/src/pages)
You'll need node and npm on your system.


## Using runner.py to test things quickly
The file `runner.py` is a quick shortcut file that allows you to run a single test quickly, without the web UI.

If you look in the `main()` function there are a bunch of commented out single calls.
I usually use this when testing something on the server code before building the web front-end.

### to run a benchmark
The minimum you need to load up the google doc data and run a benchmark

(change these values to match your agent and test set names)

```python
    configlib.refresh_agent_configs()
    configlib.fetch_gdoc_configs()
    load_test_set_gdoc("xp_meena_test")
    bench_run(agent_name='may-er', set_name='xp_meena_test')

```

# Extended installs for NLP models
The models for NLP matching etc. are very large, and usually added on the fly after deploy.
But this doesn't work on App engine since it's a read-only disc.
I got around this by downloading and unpacking the models,
ignoring them to not go into github.

This means that you need to install them yourself though if you want to deploy the app or run the NLP stuff locally.

[more info here](https://stackoverflow.com/questions/54023378/how-to-download-a-spacy-model-on-app-engine-2nd-generation)


## Spacy Models

NOTE - only needed for more experimental features

You do NOT need to install this just for testrunner etc.

I have bundled the small and medium 'en' spacy models in [data/models](data/models)

`_md` has word vectors, but semantic matching isn't as good as USE.

this is roughly equivalent to
`python -m spacy download en_core_web_md`

For the basic spAcy models, I downloaded the files from here:

https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.0.0/en_core_web_sm-3.0.0.tar.gz

https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.0.0/en_core_web_md-3.0.0.tar.gz

https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.0.0/en_core_web_lg-3.0.0.tar.gz

After downloading, I decompressed and untared them in my filesystem, e.g.

```
mv ~/Downloads/
tar -xvf /path_to_models/en_core_web_lg-3.0.0/
```

I then load a model using the explicit path and it worked from within PyCharm (note the path used goes all the way to en_core_web_lg-3.0.0; you will get an error if you do not use the folder with the config.cfg file):

`nlpObject = spacy.load('/path_to_models/en_core_web_lg-3.0.0/en_core_web_lg/en_core_web_lg-3.0.0')`

update: just do this:

`make spacy-install`

then if you deploy the files will also get deployed.


## Universal Sentence Encoder
NOTE - only needed for more experimental features

You do NOT need to install this just for testrunner etc.

Is a much better model but also brings in all of tensor-flow.
So far I only have this working locally.
Maybe later I'll deploy a version as a "USE server" on a separate VM...


If you want to use the USE models

pip install https://github.com/MartinoMensio/spacy-universal-sentence-encoder/releases/download/v0.4.3/en_use_md-0.4.3.tar.gz#en_use_md-0.4.3

more info here
https://github.com/MartinoMensio/spacy-universal-sentence-encoder

spacy-universal-sentence-encoder==0.4.3

https://github.com/MartinoMensio/spacy-universal-sentence-encoder/releases/download/v0.4.3/en_use_md-0.4.3.tar.gz


## Updating the "upstream" SAPI library
NOTE - only needed for more experimental features

You do NOT need to install this just for testrunner etc.


If you're working with a local copy of the SCRAPI lib eg for hot patches,

To apply this to your local repo:

```
rm -rf dfcx_scrapi
git submodule init
git submodule update
```

I think that should then leave you with a checkout of the SCRAPI lib, eg

`ls -la` should show `dfcx_scrapi` as a directory. You can `cd` into that directory, which is actually another git repo, and see what version is checked out.

`git status`

if it's not `master` you can force the submodule to update with

`git checkout master`

- read more about updating [submodules](https://stackoverflow.com/questions/913701/how-to-change-the-remote-repository-for-a-git-submodule)


`git submodule update --init --recursive --remote`


## Debugger

To run modify `runner.py`
