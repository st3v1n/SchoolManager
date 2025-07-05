from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from .forms import StudentSignupForm, StudentLoginForm,AdminCreationForm, TeacherCreationForm, StudentCreationForm, ParentCreationForm
from django.contrib import messages
from .models import User
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required

def test(request): return render(request, 'test.html')

def role_results(request):
    selected_role = request.GET.get('user-types', 'student')  
    print('selected role ' + selected_role)
    user_w_role = User.objects.filter(role=selected_role)

    return render(request, 'partials/role_results.html', {
        'user_w_role': user_w_role,
        'role': selected_role,
    })

ROLE_FORM_MAPPING = {
    'admin': AdminCreationForm,
    'student': StudentCreationForm,
    'teacher': TeacherCreationForm,
    'parent': ParentCreationForm
}

@require_http_methods(["GET", "POST"])
def role_ops(request, role, uid=None):
    if role not in ROLE_FORM_MAPPING:
        messages.error(request, 'Invalid role specified')
        return JsonResponse({'error': 'Invalid role'}, status=400)

    FormClass = ROLE_FORM_MAPPING[role]
    user = get_object_or_404(User, id=uid, role=role) if uid else None

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES or None, instance=user)

        if form.is_valid():
            try:
                user = form.save()
                action = "edited" if uid else "created"
                messages.success(request, f'{role.capitalize()} {action} successfully.')

                user_w_role = User.objects.filter(role=role).select_related(
                    'student_profile', 'teacher_profile', 'parent_profile'
                )
                

                context = {
                    'user_w_role': user_w_role,
                    'role': role,
                }

                response = HttpResponse(
                    render(request, 'partials/role_results.html', context)
                )
                response['HX-Trigger'] = 'showMessage'
                return response

            except ValidationError as e:
                form.add_error(None, str(e))
                print(e, 'as v')
            except Exception as e:
                print(e, 'as e')
                form.add_error(None, f"An error occurred while saving the {role}")
    else:
        form = FormClass(instance=user)

    context = {
        'form': form,
        'is_editing': bool(uid),
        'role': role,
    }
    return render(request, 'partials/form_create_user.html', context)

def search_users(request):
    query = request.GET.get('q', '')
    field_type = request.GET.get('field', '')
    print('field type:', field_type, 'query:', query)

    users = []

    if field_type == 'parents':
        users = User.objects.filter(
            role='parent',
            is_active=True
        ).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )[:10]
    elif field_type == 'children':
        users = User.objects.filter(
            role='student',
            is_active=True
        ).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )[:10]

    users_data = [{
        'id': user.id,
        'name': f"{user.first_name} {user.last_name}",
        'email': user.email,
        'avatar': user.profile_picture.url if user.profile_picture else '/static/images/default-avatar.png'
    } for user in users]
    context = {
        'users_data': users_data
    }

    return render(request, 'partials/search_results.html', context)

@login_required(login_url='login')
def dashboard(request): 
    USERROLES = User.USER_ROLES
    context = {
        'user_roles': USERROLES,
        'role': 'student'
    }
    return render(request,'dashboard.html', context)

def login_view(request):
    if request.method == 'POST':
        form = StudentLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard') 
    else:
        form = StudentLoginForm()
    return render(request, 'login.html', {'login_form': form})

def signup_view(request):
    if request.method == 'POST':
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Success, Your account has been created')
            return redirect('login_view') 
        else: print('form error :', form.errors)
    else:
        form = StudentSignupForm()
    return render(request, 'signup.html', {'signup_form': form})

def ulogout(request): 
    logout(request)
    return redirect('login')     