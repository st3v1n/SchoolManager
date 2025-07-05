from .models import Exam, Folder
from django import forms


class SaveExam(forms.ModelForm):
    # question_data = forms.CharField(widget=forms.HiddenInput())
    class Meta:
        model = Exam
        fields = '__all__'
        fields = ["folder","title", "subject", "grade_level", "paper_type", "total_marks","window_start", "window_end", "duration", "instructions", "status", "is_active", "shuffle_options", "status", "student_question_limit"]
        widgets = {
            'window_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'window_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'duration': forms.TextInput(attrs={'placeholder': ' ie HH:MM:SS'}),
            'title': forms.TextInput(attrs={'placeholder': 'An Optional title for exam'}),
            'instructions': forms.Textarea(attrs={'rows': 4}),
        }

    # subject = forms.CharField(widget=forms.TextInput(attrs={'list': 'subject-list', 'placeholder': 'Start typing the subject'}))


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].widget.attrs.update({"list": "subject_list"})
        self.fields["status"].initial = Exam.STATUS_CHOICE[1][0]
        for field in self.fields.values():
            field.widget.attrs['class'] = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"

class CreateFolder(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ["name", "parent"]
