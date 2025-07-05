from django.db import models
from django.core.exceptions import ValidationError

class AcademicYear(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name
class Term(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, db_index=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_date__lt=models.F('end_date')),
                name='check_term_start_end_date'
            ),
            models.UniqueConstraint(    
                fields=['academic_year', 'name'],
                name='unique_term_per_academic_year'
            )
        ]
    def clean(self):
        overlapping_terms = Term.objects.filter(
            academic_year=self.academic_year,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        )
        if overlapping_terms.exists() and self.pk != overlapping_terms.first().pk:
            raise ValidationError("The term dates overlap with an existing term.")
    def __str__(self):
        return f"{self.name} - {self.academic_year}"
class Grade(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
class Subject(models.Model):
    name = models.CharField(max_length=100, db_index=True)

#     code = models.CharField(max_length=20, unique=True)
#     description = models.TextField(blank=True)
#     credits = models.IntegerField()
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.name} ({self.code})"
    def __str__(self):
        return self.name
