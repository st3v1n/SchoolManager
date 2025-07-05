from django.contrib import admin
from .models import Exam, Question, ExamResult, QuestionOption


admin.site.register(Question)


class ExamAdmin(admin.ModelAdmin):
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        # Custom delete logic to handle related objects
        for exam in queryset:
            # Delete related ExamResult objects first
            exam.examresult_set.all().delete()
            # Now delete the Exam
            exam.delete()
        self.message_user(request, "Selected exams and related results have been deleted.")

    delete_selected.short_description = "Delete selected exams and related results"

admin.site.register(Exam, ExamAdmin)

admin.site.register(QuestionOption)
admin.site.register(ExamResult)