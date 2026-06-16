release: python manage.py migrate && python manage.py init_app
web: gunicorn config.wsgi:application
