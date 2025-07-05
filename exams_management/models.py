# exam_management/models.py
from django.db import models
from django.core.exceptions import ValidationError
from school_management.models import Grade, Subject
from django.utils import timezone

class Folder(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    # color = models.CharField(max_length=7, default='#007bff')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)  

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'parent'], name='unique_folder_name_per_parent')
        ]
    def clean(self):
        if self.parent and self.parent == self:
            raise ValidationError("A folder cannot be its own parent.")

    def __str__(self):
        return self.name

# class QuestionOption(models.Model):
#     question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='options')
#     option_text = models.TextField(null=True, blank=True)
#     media = models.FileField(upload_to='questions/options/media/', null=True, blank=True)
#     is_correct = models.BooleanField(default=False)

#     def __str__(self):
#         return self.option_text or f"Option for {self.question.id}"

# class Question(models.Model):
#     question_text = models.TextField()
#     question_type = models.CharField(max_length=50, choices=[
#         ('multiple_choice', 'Multiple Choice'),
#         ('true_false', 'True/False'),
#         ('FIB', 'Fill in the Blanks'),
#         ('essay', 'Essay'),
#     ])
#     marks = models.PositiveIntegerField(default=1)
#     media = models.FileField(upload_to='questions/', null=True, blank=True)
#     # correct_option = models.ForeignKey(QuestionOption, on_delete=models.SET_NULL, null=True, blank=True)

#     def clean(self):
#         if self.question_type == 'multiple_choice' and not self.correct_option:
#             raise ValidationError("Multiple-choice questions must have a correct option.")
#         if self.correct_option and self.correct_option.question != self:
#             raise ValidationError("Correct option must be one of the provided options.")

#     def __str__(self):
#         return self.question_text


class Question(models.Model):
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=[
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('FIB', 'Fill in the Blanks'),
        ('essay', 'Essay'),
    ])
    marks = models.PositiveIntegerField(default=1)
    media = models.FileField(upload_to='questions/', null=True, blank=True)

    def clean(self):
        if self.question_type == 'multiple_choice' and not self.options.filter(is_correct=True).exists():
            raise ValidationError("Multiple-choice questions must have a correct option.")

    def __str__(self):
        return self.question_text

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options', null=True)
    option_text = models.TextField(null=True, blank=True)
    media = models.FileField(upload_to='questions/options/media/', null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option_text or f"Option for {self.question.id}"
    
class Exam(models.Model):
    STATUS_CHOICE = [('draft', 'Draft'), ('complete', 'Complete')]
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, blank=True, null=True, db_index=True)
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, db_index=True)
    paper_type = models.CharField(max_length=15, choices=[('test', 'Test'), ('practice', 'Practice'), ('assignment', 'Assignment'), ('exam', 'Exam')], db_index=True)
    grade_level = models.ForeignKey(Grade, on_delete=models.CASCADE, db_index=True)
    window_start = models.DateTimeField(blank=True, null=True) 
    window_end = models.DateTimeField(blank=True, null=True)   
    duration = models.DurationField(null=True, blank=True)  
    instructions = models.TextField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    shuffle_options = models.BooleanField(default=False)
    student_question_limit = models.PositiveIntegerField(default=0, help_text="How many questions a student should answer.")
    questions = models.ManyToManyField(Question)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICE,
        default='draft'
    )
    total_marks = models.PositiveIntegerField(default=0, blank=True, null=True) # add this field if you want to store it.

    def clean(self):
        """Custom validation for time-based and duration-based access."""
        if self.window_start and self.window_end:
            if self.window_start >= self.window_end:
                raise ValidationError("Window start time must be earlier than the window end time.")
        if self.window_start and not self.window_end and not self.duration:
            raise ValidationError("Window end time or duration must be provided if window start time is set.")
        if self.window_end and self.window_end < timezone.now():
            self.is_active = False 


    # @property
    # def calculate_total_marks(self):
    #     return sum(question.marks for question in self.questions.all())

    def save(self, *args, **kwargs):
        # is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # if is_new and not self.student_question_limit:
        #     self.student_question_limit = self.questions.count()
        #     super().save(update_fields=['student_question_limit'])

    def __str__(self):
        return f"{self.subject} {self.paper_type} - Class: {self.grade_level}"

class ExamResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question, blank=True)
    student = models.ForeignKey('core.User', on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True) 
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    highest_score = models.IntegerField(null=True, blank=True)
    def calculate_score(self):
        etm = self.exam.total_marks
        correct_answers = sum(
            1 for answer in self.answers.all()
            if answer.selected_option and answer.selected_option.is_correct
        )
        self.highest_score = etm
        total_score = (correct_answers * etm) / self.exam.student_question_limit
        return round(total_score, 2)




    def has_expired(self):
        if self.submitted_at:
            return True
        elapsed = timezone.now() - self.start_time
        return elapsed.total_seconds() > self.exam.duration.total_seconds()

class ExamAnswer(models.Model):
    attempt = models.ForeignKey(ExamResult, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ('attempt', 'question')
        
    def __str__(self):
        return f"{self.attempt.student.username} - {self.question.question_text[:30]}"
        