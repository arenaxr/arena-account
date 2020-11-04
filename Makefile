PYTHON3=/usr/local/bin/python3 
PIP3=/usr/local/bin/pip3

run: env
	. env/bin/activate; ${PYTHON3} manage.py runserver

env: env/bin/activate FORCE

env/bin/activate: requirements.txt
	test -d env || virtualenv -p ${PYTHON3} env
	. env/bin/activate; ${PIP3} install -Ur requirements.txt
	touch env/bin/activate

test: env
	. env/bin/activate; ${PYTHON3} manage.py test

migrate: env
	. env/bin/activate; ${PYTHON3} manage.py makemigrations; ${PYTHON3} manage.py migrate; 

clean:
	rm -rf env
	find -iname "*.pyc" -delete


FORCE:
