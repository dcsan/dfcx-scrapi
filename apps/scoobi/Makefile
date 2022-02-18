
## default task
cli: cls
	python3 cli.py

show-data:
	cat data/ignored/sample.csv

# remove old csv samples
clean:
	rm data/ignored/*csv

run: cli show-data

freeze:
	pip freeze > requirements.txt

cls:
	clear && printf '\e[3J'
	@echo '--'

test: cls
	pytest -v

lint:
	mypy .


# use a local copy of scrapi lib
local-scrapi:
	pip install ../../python-dialogflow-cx-high-level-api
