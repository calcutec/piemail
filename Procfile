web: gunicorn heroku:app --log-file=-
init: python db_create.py
upgrade: python db_upgrade.py