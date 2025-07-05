from django.test import TestCase
from .models import Grade
class GradeCheck(TestCase):
    def cheker():
        print('grades checker initialized')
        grades = Grade.objects.all()
        print(grades)