#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line
from waitress import serve

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmanager.settings')
django.setup()

# Import your Django WSGI application
from schoolmanager.wsgi import application

if __name__ == '__main__':
    # Run with Waitress WSGI server
    print("Starting Django application with Waitress...")
    serve(application, host='0.0.0.0', port=8000)
