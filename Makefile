check-format:
	pre-commit run -a
format: check-format
coverage:
	coverage run -m pytest && coverage report -m
test:
	pytest -vv