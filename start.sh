#!/bin/bash
cd /var/www/pea
source venv/bin/activate
screen -dmS pea python3 src/manage.py runserver 0.0.0.0:80
