release: python manage.py migrate && python manage.py seed_prueba
web: gunicorn config.wsgi:application
