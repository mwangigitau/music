install:
	#install
	pip install --upgrade pip &&\
	pip install -r requirements.txt
format:
	#format
	black *.py app/*.py
lint:
	#pylint
	pylint --disable=R,C *.py app/*.py
test:
	#testing
	python3 -m pytest -vv --cov=app --cov=main test_*.py
build:
	#build containers
	docker compose up --build
deploy:
	#deploy
all: install format lint test deploy
