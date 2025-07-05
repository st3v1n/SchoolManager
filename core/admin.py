from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import AdminCreationForm, TeacherCreationForm, StudentCreationForm, ParentCreationForm
from .models import StudentProfile, TeacherProfile, ParentProfile, User
# # admin.site.register(User)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(ParentProfile)

# class CustomUserAdmin(UserAdmin):
#     model = User
#     add_form = AdminCreationForm
#     form = AdminCreationForm
#     list_display = ['email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']
#     search_fields = ['email', 'first_name', 'last_name']
#     ordering = ['email']

#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture', 'role')}),
#         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login',)}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
#         }),
#     )

#     def save_model(self, request, obj, form, change):
#         """Override to automatically create or update profiles."""
#         super().save_model(request, obj, form, change)
        
#         # Create or update profile based on the user's role
#         if obj.role == 'teacher' and not hasattr(obj, 'teacher_profile'):
#             TeacherProfile.objects.get_or_create(user=obj)
#         elif obj.role == 'student' and not hasattr(obj, 'student_profile'):
#             StudentProfile.objects.get_or_create(user=obj)
#         elif obj.role == 'parent' and not hasattr(obj, 'parent_profile'):
#             ParentProfile.objects.get_or_create(user=obj)
# admin.site.register(User, CustomUserAdmin)

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    list_filter = ['is_staff', 'is_superuser', 'role']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )
admin.site.register(User, CustomUserAdmin)
