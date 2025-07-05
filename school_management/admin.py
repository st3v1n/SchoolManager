from django.contrib import admin
from .models import Subject, Grade, Term
admin.site.register(Subject)
admin.site.register(Term)
admin.site.register(Grade)