f ?= somefile.py
GCP_TOKEN ?= $(shell gcloud auth print-identity-token)

# replace this to automate commands below
PROJ_NAME ?= "TODO-your-gcp-project"


# default target
runner: cls run-bench
	# python cust_run.py

run-log: cls
	rm logs/run.log
	python runner.py 2&> logs/run.log

run-load: cls
	python cust_run.py load

run-graph: cls
	python cust_run.py graph

run-qa:
	python cust_run.py qa

run-bench: cls
	python cust_run.py bench

run-meena: cls
	python cust_run.py meena

build-meena-map:
	python cust_run.py meena
	cp data/meena/meena_map.json ../dc-external-verizon-repo/mefunc

view-log:
	less -r logs/run.log

run-view: run-log view-log

tail-log:
	tail -f logs/run.log

cls:
	clear && printf '\e[3J'
	@echo 'cleared'


# for google cloud shell
python-setup:
	@echo "# these commands have to be run in the current shell"
	@echo "sudo apt-get install python3-venv"
	@echo "python3 -m venv venv"
	@echo "---- stop and type into the shell ----"
	@echo "source venv/bin/activate"
	@echo "pip3 install --upgrade pip"
	@echo "python3 -m pip install --upgrade setuptools"
	@echo "pip install -r requirements.txt"

first:
	pip install google-cloud-dialogflow-cx

pinstall:
	pip install -r requirements.txt

freeze:
	pip freeze | grep -vE "pkg-resources|pytype|en-use-md|en-core-web" > requirements.txt

freeze-dev:
	@echo "freezing to requirements-dev.txt so we don't require all development modules in gcloud runtime"
	pip freeze > requirements-dev.txt

# freeze-clean:
# 	echo requirements.txt > grep -vE "pkg-resources|pytype|"

# use it like
# make autofix f=somefile.py
lintfix:
	autopep8 --aggressive --aggressive --verbose --in-place ${f}

lint:
	pylint

hints:
	mypy cxutils/digger/chat_stat.py

# static server just to view assets
# not really needed now
static-server:
	python3 -m http.server -d public/ 8080

# run flask server locally
server: cls
	python main.py

## ----------------------------- app engine -----------------------------


# run full appengine env
gae-run-local:
	dev_appserver.py ./

# run the flask server on 4000
flask-run-local:
	python main.py

## ----------------- google cloud funcs stuff -----------------

# login to gcp and get new creds
gcp-login:
	gcloud auth login
	gcloud config set project $(PROJ_NAME)

gcp-check-proj:
	gcloud config get-value project

#  --quiet = no prompt
# --verbosity=info
gae-deploy:
	@echo "-- this will just deploy without client build"
	gcloud app deploy --quiet --promote

gae-deploy-cron:
	gcloud app deploy cron.yaml --quiet

glogs:
	@echo "---- gcp logs ----"
	gcloud app logs tail -s default

gcp-set-proj:
	gcloud config set project $(PROJ_NAME)

describe-deployed:
	gcloud functions describe webhook

cloud-logs:
	# gcloud functions logs read webhook
	gcloud logging read "resource.type=gae_app" --project=$(PROJ_NAME)



## client
build-client:
	cd client && npm run build

# shortcuts

deploy:	gcp-set-proj gcp-check-proj build-client gae-deploy gae-deploy-cron wake-up

# first request to wake the bot after deploy
wake-up:
	curl "https://$(PROJ_NAME).wl.r.appspot.com/kzen"

# not that quick but skip building client
quick-deploy: gae-deploy gae-deploy-cron # gae-logs
qd: quick-deploy

cf-deploy: cls
	gcloud functions deploy sheet_runner --runtime python38 --trigger-http

# run webserver
cf-run-local:
	functions_framework --target=webhook

plain-request:
	curl localhost:8080?name=bob

json-request:
	curl -X POST localhost:8080 -H "Content-Type:application/json"  -d '{"name":"Charlie"}'


# @echo "using token $(GCP_TOKEN)"
remote-test:
	@curl https://us-central1-$(PROJ_NAME).cloudfunctions.net/sheet_runner?name=runner-test -H "Authorization: Bearer $(GCP_TOKEN)"

check-token:
	@echo "using token $(GCP_TOKEN)"

# spacy models install
spacy-download:
	rm -f data/models/*gz
	wget -P data/models \
		https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.0.0/en_core_web_lg-3.0.0.tar.gz

	wget -P data/models \
		https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.0.0/en_core_web_md-3.0.0.tar.gz

	wget -P data/models \
		https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.0.0/en_core_web_sm-3.0.0.tar.gz

spacy-unpack:
	cd data/models && tar -xvf en_core_web_lg-3.0.0.tar.gz
	cd data/models && tar -xvf en_core_web_md-3.0.0.tar.gz
	cd data/models && tar -xvf en_core_web_sm-3.0.0.tar.gz


spacy-install: spacy-download spacy-unpack

# universal sentence encoder
use-install:
	pip install https://github.com/MartinoMensio/spacy-universal-sentence-encoder/releases/download/v0.4.3/en_use_md-0.4.3.tar.gz#en_use_md-0.4.3

# testing
# pytest tests/configlib_test.py --disable-pytest-warnings
# pytest tests --disable-pytest-warnings
# python3 -m pytest tests/chat_log_test.py
test: cls
	python3 -m pytest

# test watch - requires pytest
watch:
	ptw --ignore ./dfcx_scrapi --ignore ./venv --disable-pytest-warnings

# to install your own local copy of scrapi from parent directory
local-scrapi:
	pip install ../python-dialogflow-cx-high-level-api

update-scrapi:
	pip uninstall -y dfcx-scrapi
	pip install dfcx-scrapi


test-cron:
	# curl "http://localhost:4000/api/cron/goldset?sample=10"
	curl "http://localhost:4000/api/cron/goldset"
