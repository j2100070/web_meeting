#!/bin/sh
python manage.py makemigrations  --noinput
python manage.py migrate  --noinput

# 環境変数のDEBUGの値がTrueの時はrunserverを、Falseの時はgunicornを実行します
if [ $DEBUG = "True" ]
then
    python manage.py runserver 0.0.0.0:8000
else
    # gunicornを起動させる時はプロジェクト名を指定します
    python manage.py collectstatic --noinput
    gunicorn --workers=9 --timeout 120 mtgsys.wsgi:application --bind 0.0.0.0:8000
fi
