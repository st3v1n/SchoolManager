from django.db import migrations
import logging
logger = logging.getLogger(__name__)

def migrate_grade_level(apps, schema_editor):
    StudentProfile = apps.get_model('core', 'StudentProfile')
    Grade = apps.get_model('school_management', 'Grade')

    for student in StudentProfile.objects.all():
        grade_name = student.grade_level.strip()
        try:
            grade = Grade.objects.get(name=grade_name)
            logger.warning(f"{student} is set to grade: {grade}")
            student.grade_level_fke = grade
            student.save()
        except Grade.DoesNotExist:
            pass  # Optionally log missing grades

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_studentprofile_grade_level_fke_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_grade_level),
    ]
