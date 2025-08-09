from django.shortcuts import render, redirect, get_object_or_404
from .forms import SaveExam, CreateFolder
from django.views.decorators.http import require_POST
from .models import Question, Folder, QuestionOption, Exam, Subject, Grade, ExamAnswer, ExamResult
from core.models import StudentProfile
import json
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.paginator import Paginator
from django.db.models import Case, When, IntegerField, Q
from random import sample

def create(request):
    return render(request, 'format_exam.html', {
        'editing': False
    })

def exam_list(request):
    search_query = request.GET.get('search', '')
    print('query: ', search_query)
    exams = Exam.objects.annotate(
        is_active_order = Case(
            When(is_active=True, then=0), 
            default=1,
            output_field=IntegerField()
        )
    ).order_by('is_active_order', '-created_at')

    if search_query:
        exams = exams.filter(
            Q(title__icontains=search_query) |
            Q(subject__name__icontains=search_query) |
            Q(paper_type__icontains=search_query) |
            Q(grade_level__name__icontains=search_query)
        )


    paginator = Paginator(exams, 15)

    page_number = request.GET.get("page")
    exams = paginator.get_page(page_number)

    context = {
        'exams': exams,
        'search_query': search_query
    }
    return render(request, 'partials/exam_list.html', context)

def save_exam(request, exam_id=None):
    exam = None
    if exam_id:
        exam = get_object_or_404(Exam, id=exam_id)

    if request.method == "POST":
        form = SaveExam(request.POST, instance=exam)
        if form.is_valid():
            try:
                with transaction.atomic():
                    exam = form.save()

                    questions_data = json.loads(request.POST.get('exam_questions', '[]'))

                    if exam_id:
                        exam.questions.all().delete()

                    question_objects = []
                    for question_data in questions_data:
                        question = Question.objects.create(
                            question_text=question_data.get("content", ""),
                            question_type=question_data.get("type", "multiple_choice"),
                            marks=int(question_data.get("marks", 1))
                        )

                        if "options" in question_data:
                            for option_data in question_data["options"]:
                                QuestionOption.objects.create(
                                    question=question,
                                    option_text=option_data.get("text", ""),
                                    is_correct=option_data.get("correct", False)
                                )

                        question_objects.append(question)

                    exam.questions.add(*question_objects)
                    exam.save()

                    # return JsonResponse({"message": "Exam saved successfully!", "exam_id": exam.id})
                    return render(request, 'partials/exam_success.html')

            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON data in exam_questions."}, status=400)

    context = {'form': SaveExam(instance=exam),'exam': exam, }
    return render(request, 'partials/form_save_exam.html', context)

def save_question(request, exam_id):    
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == "POST":
        question_data = json.loads(request.body)
        question = Question.objects.create(
            question_text=question_data.get("content", ""),
            question_type=question_data.get("type", "multiple_choice"),
            marks=int(question_data.get("marks", 1))
        )

        if "options" in question_data:
            for option_data in question_data["options"]:
                QuestionOption.objects.create(
                    question=question,
                    option_text=option_data.get("text", ""),
                    is_correct=option_data.get("correct", False)
                )

        exam.questions.add(question)
        exam.save()

        return JsonResponse({"message": "Question added successfully!"})

    return JsonResponse({"error": "Invalid request method."}, status=405)

@require_POST
def toggle_exam_active(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    exam.is_active = not exam.is_active
    exam.save()
    
    # Render the updated toggle HTML
    html = render_to_string('partials/toggle.html', {
        'exam': exam,
        'field': 'is_active',
        'checker': exam.is_active,
        'label': 'Is Active',
        'deurl': '{% url "exam:toggle_exam_active" exam.id %}',
    })
    return HttpResponse(html)

@require_POST
def toggle_exam_shuffle(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    exam.shuffle_options = not exam.shuffle_options
    exam.save()

    html = render_to_string('partials/toggle.html', {
        'field': 'is_shuffle',
        'checker': exam.shuffle_options,
        'label': 'Exam Shuffle',
        'deurl': '{% url "exam:toggle_exam_shuffle" exam.id %}',
    })
    return HttpResponse(html)

def question_info(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    context = {
        'exam': exam,   
    }
    return render(request, 'partials/question_info.html', context)

def update_student_question_limit(request, exam_id):
    if request.method == "POST":
        exam = get_object_or_404(Exam, id=exam_id)
        student_question_limit = request.POST.get('student_question_limit')
        total_marks = request.POST.get('total_marks')

        print('request: ', request)
        print('student_question_limit: ', student_question_limit)
        print('total_marks: ', total_marks)
        try:
            if total_marks:
                exam.total_marks = total_marks
            if student_question_limit:
                exam.student_question_limit = student_question_limit
            exam.save()
        except Exception as e:
            print(e)
        except ValidationError as v:
            print(v)

        response = HttpResponse()
        response['HX-Trigger'] = "StudentLimitUpdate"
        return response
    
def delete(request, exam_id):
    if request.method == "DELETE":
        exam = get_object_or_404(Exam, id=exam_id)
        exam.delete()
        return redirect('exam:exam_list')

def edit(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()    
    return render(request, 'format_exam.html', {
        'exam': exam,
        'questions': questions,
        'editing': True if exam else False
    })

@login_required
@ensure_csrf_cookie
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    student = request.user
    
    attempt = ExamResult.objects.filter(exam=exam, student=student).first()
    
    if attempt:
        if attempt.submitted_at:
            messages.error(request, "You have already completed this exam. Only one attempt is allowed.")
            return redirect('dashboard')
        
        # Check if time has expired
        if attempt.has_expired():
            attempt.score = attempt.calculate_score()
            attempt.submitted_at = timezone.now()
            attempt.save()
            messages.error(request, "Your exam time has expired.")
            return redirect('exam:exam_results', attempt_id=attempt.id)
        
        # Continue existing attempt
        elapsed = timezone.now() - attempt.start_time
        if not exam.duration:
            messages.error(request, "This exam has no duration set.")
            return redirect('dashboard')

        remaining_seconds = max(0, exam.duration.total_seconds() - elapsed.total_seconds())
        
        return render(request, 'take_exam.html', {
            'exam': exam,
            'attempt_id': attempt.id,
            'selected_questions':attempt.questions.all(),
            'remaining_time': int(remaining_seconds),
            'duration': exam.duration.total_seconds(),
            'start_time': attempt.start_time.isoformat()  # Pass server-side start time
        })
    
    # Check exam availability
    current_time = timezone.now()
    if exam.window_start and current_time < exam.window_start:
        messages.error(request, "This exam is not available yet.")
        return redirect('dashboard')
    if exam.window_end and current_time > exam.window_end:
        messages.error(request, "This exam is no longer available.")
        return redirect('dashboard')
    
    num_questions = exam.student_question_limit
    all_questions = list(exam.questions.all())
    
    if num_questions > len(all_questions):
        messages.error(request, "Not enough questions in the paper.")
        return redirect('dashboard')

    selected_questions = sample(all_questions, num_questions)
    attempt = ExamResult.objects.create(
        exam=exam,
        student=student,
        start_time=timezone.now(),
        score=None
    )
    
    attempt.questions.add(*selected_questions)

    return render(request, 'take_exam.html', {
        'exam': exam,
        'selected_questions':attempt.questions.all(),
        'attempt_id': attempt.id,
        'remaining_time': int(exam.duration.total_seconds()),
        'duration': exam.duration.total_seconds(),
        'start_time': attempt.start_time.isoformat()
    })

@login_required
@transaction.atomic
def submit_exam(request, attempt_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    
    attempt = get_object_or_404(ExamResult, 
                              id=attempt_id, 
                              student=request.user,
                              submitted_at__isnull=True)
    
    # Check if time has expired
    if attempt.has_expired():
        attempt.score = attempt.calculate_score()
        attempt.submitted_at = timezone.now()
        attempt.save()
        return JsonResponse({
            'status': 'timeout',
            'message': 'Time expired',
            'score': attempt.score,
            'redirect_url': f'/exam/results/{attempt_id}/'
        })
    
    try:
        data = json.loads(request.body)
        answers = data.get('answers', {})
        
        for question_id, option_id in answers.items():
            question = attempt.exam.questions.get(id=question_id)
            option = QuestionOption.objects.get(id=option_id)
            if not question.options.filter(id=option.id).exists():
                return JsonResponse({'status': 'error', 'message': 'Invalid option selected.'}, status=400)

            ExamAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={'selected_option': option}
            )
        
        attempt.score = attempt.calculate_score()
        attempt.submitted_at = timezone.now()
        attempt.save()
        
        return JsonResponse({
            'status': 'success',
            'score': attempt.score,
            'redirect_url': f'/exam/results/{attempt_id}/'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def exam_results(request, attempt_id):
    attempt = get_object_or_404(ExamResult, id=attempt_id, student=request.user)
    
    if attempt.submitted_at is None:
        messages.error(request, "This exam has not been submitted yet.")
        return redirect('dashboard')
    
    user_answers = {}
    correct_question_ids = {}
    try:
        answers = ExamAnswer.objects.filter(attempt=attempt)
        for answer in answers:
            user_answers[str(answer.question.id)] = str(answer.selected_option.id)
    except Exception as e:
        messages.error(request, f"Error retrieving answers: {str(e)}")
        user_answers = {}
    
    total_questions = attempt.questions.count()
    correct_answers = 0
    
    # Count correct answers
    for question in attempt.exam.questions.all():
        question_id_str = str(question.id)
        if question_id_str in user_answers:
            selected_option_id = user_answers[question_id_str]
            is_correct = question.options.filter(id=selected_option_id, is_correct=True).exists()
            correct_question_ids[question_id_str] = is_correct
        else:
            correct_question_ids[question_id_str] = False
    percentage = (attempt.score / attempt.exam.total_marks) * 100 if attempt.exam.total_marks > 0 else 0
    correct_answers = sum(1 for correct in correct_question_ids.values() if correct)

    
    context = {
        'attempt': attempt,
        'selected_questions': attempt.questions.all(),
        'exam': attempt.exam,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'percentage': percentage,
        'user_answers': user_answers,
        'correct_question_ids': correct_question_ids,
    }
    
    return render(request, 'exam_review.html', context)

def results(request):
    role = request.user.role

    search_query = request.GET.get('search', '')

    if role == 'student': results = ExamResult.objects.filter(student=request.user)
    # elif role == 'teacher': results = ExamResult.objects.filter(exam__subject__in=request.user.teaching_subjects.all())
    else: results = ExamResult.objects.all()    

            # move this params to filter instead of search 
            # add date and time filters
            # Q(student__student_profile__grade_level__icontains=search_query) |
            # Q(exam__paper_type__icontains=search_query) |
    if search_query:
        results = results.filter(
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__email__icontains=search_query) |
            Q(exam__subject__name__icontains=search_query)
        )

    results = results.order_by('-submitted_at')
    paginator = Paginator(results, 15)


    page_number = request.GET.get("page")
    results = paginator.get_page(page_number)
        
    return render(request, 'results.html', context={'results':results, 'result_search_query': search_query})

@login_required
@require_POST
def ping(request, attempt_id):
    attempt = get_object_or_404(ExamResult, id=attempt_id, student=request.user, submitted_at__isnull=True)
    # last_activity is automatically updated due to auto_now=True
    return JsonResponse({'status': 'ok'})

def active_papers(request):
    if request.user.is_authenticated:
        grade_level = request.user.student_profile.grade_level
        papers = Exam.objects.filter(is_active=True, grade_level=Grade.objects.get(name=grade_level))
    return render(request, 'partials/active_papers.html', {'papers': papers})

def exam_ready(request, exam_id):
    return render(request, 'partials/exam_ready.html', context={
        'instructions' : Exam.objects.get(id=exam_id).instructions,
        'examid': exam_id
    })

def get_folder_structure(request):
    def build_tree(folder):
        return {
            'id': folder.id,
            'name': folder.name,
            # 'color': folder.color,
            'children': [build_tree(child) for child in folder.children.all()],
            'exams': [{'id': exam.id, 'subject': exam.subject.name, 'paper_type': exam.paper_type} for exam in folder.exam_set.all()]
        }

    root_folders = Folder.objects.filter(parent__isnull=True)
    structure = [build_tree(folder) for folder in root_folders]
    root_exams = Exam.objects.filter(folder__isnull=True)
    structure.append({
        'id': None,
        'name': 'Top',
        'children': [],
        'exams': [{'id': exam.id, 'subject': exam.subject.name, 'paper_type': exam.paper_type} for exam in root_exams]
    })
    # print(structure)
    return JsonResponse(structure, safe=False)

def folder_operations(request, folder_id=None):
    folder = None
    if folder_id:
        folder = get_object_or_404(Folder, id=folder_id)

    if request.method == "POST":
        form = CreateFolder(request.POST, instance=folder)
        if form.is_valid():
            form.save()
        response = HttpResponse()
        response['HX-Trigger'] = "folderChanged"
        return response

    elif request.method == "DELETE":
        if folder:
            folder.delete()
        response = HttpResponse()
        response['HX-Trigger'] = "folderChanged"
        return response

    else:  # GET or other
        form = CreateFolder(instance=folder)
        context = {'form': form, 'folder': folder}
        return render(request, 'partials/form_folder.html', context)
