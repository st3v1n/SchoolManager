from django.db import migrations

def migrate_grade_level(apps, schema_editor):
    StudentProfile = apps.get_model('core', 'StudentProfile')
    Grade = apps.get_model('school_management', 'Grade')

    for student in StudentProfile.objects.all():
        grade_name = student.grade_level.strip()
        try:
            grade = Grade.objects.get(name=grade_name)
            student.grade_level_fke = grade
            student.save()
            print(f"{student} → {grade_name} → {grade.id}")
        except Grade.DoesNotExist:
            print(f"[WARNING] Grade '{grade_name}' not found for student: {student.user.get_full_name()}")

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20250512_2341'),
    ]

    operations = [
        migrations.RunPython(migrate_grade_level),
    ]
