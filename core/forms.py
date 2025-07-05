from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import StudentProfile, TeacherProfile, ParentProfile, User
from school_management.models import Grade, Subject
from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinLengthValidator
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

class SearchableUserSelectWidget(forms.SelectMultiple):
    template_name = 'widgets/searchable_user_select.html'

    def __init__(self, attrs=None, choices=(), field_type=None):
        super().__init__(attrs, choices=choices)
        self.field_type = field_type or ''  # 'parents' or 'children'

    def format_value(self, value):
        """Format the initial value as a list of profile objects."""
        if not value:
            return []
        
        queryset = getattr(self.choices, 'queryset', None)
        
        if queryset is not None:
            if isinstance(value, (list, tuple)) and value and hasattr(value[0], 'pk'):
                # Already a list of model instances
                return value
                
            # Convert IDs to a list if necessary
            if isinstance(value, str):
                value = value.split(',') if value else []
            elif not isinstance(value, (list, tuple)):
                value = [value]
                
            cleaned_ids = []
            for v in value:
                try:
                    if v and str(v).strip():
                        cleaned_ids.append(int(v))
                except (ValueError, TypeError):
                    pass 
            
            if cleaned_ids:
                return queryset.filter(pk__in=cleaned_ids)
        
        return []

    def get_context(self, name, value, attrs):
        value = self.format_value(value)
        attrs = self.build_attrs(self.attrs, attrs or {})
        attrs.setdefault('id', f'id_{name}')

        # Ensure we have full profile objects with user data for display
        formatted_value = []
        for item in value:
            if hasattr(item, 'user'):
                # It's a ParentProfile
                formatted_value.append(item)
            elif hasattr(item, 'parent_profile'):
                # It's a User with parent_profile
                formatted_value.append(item.parent_profile)
            
        context = {
            'widget': {
                'name': name,
                'value': formatted_value,  
                'attrs': attrs,
                'field_type': self.field_type,
            }
        }
        return context

    def value_from_datadict(self, data, files, name):
        """
        Extract user IDs from submitted form data.
        For a multi-select field, Django expects a list of values.
        """
        if name not in data:
            return []
        
        values = data.getlist(name)
        result = []
        for v in values:
            try:
                if v and str(v).strip():
                    result.append(int(v))
            except (ValueError, TypeError):
                pass 
                
        return result

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        html = render_to_string(self.template_name, context)
        return mark_safe(html)

class FormStyleMixin:
    """Mixin to add consistent styling to form fields."""
    
    def add_css_classes(self):
        """Add common CSS classes to all fields."""
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                field.widget.attrs.update({
                    'class': 'h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary'
                })

class PasswordHandlingMixin:
    """Mixin to handle password validation and optional passwords for edits."""

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        # Editing: allow blank passwords if unchanged
        if self.instance and self.instance.pk:
            if not password1 and not password2:
                return password2
            if password1 != password2:
                raise ValidationError(_("Passwords do not match"))
        else:
            # Creating new user
            if not password1 or not password2:
                raise ValidationError(_("Both password fields are required"))
            if password1 != password2:
                raise ValidationError(_("Passwords do not match"))

        return password2

    def setup_password_fields(self):
        """Make password fields optional if editing an existing user."""
        if self.instance and self.instance.pk:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].help_text = _("Leave blank if not changing password")
            self.fields['password2'].help_text = _("Leave blank if not changing password")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if self.instance and self.instance.pk:
            if not password1 and not password2:
                self._errors.pop('password1', None)
                self._errors.pop('password2', None)
                cleaned_data.pop('password1', None)
                cleaned_data.pop('password2', None)
        return cleaned_data

class RoleMixin:
    """Mixin to handle setting the user role."""
    
    def set_role(self, role):
        """Set the role as a hidden field with validation."""
        if role not in dict(User.USER_ROLES).keys():
            raise ValueError(_('Invalid role provided'))
        self.fields['role'].initial = role
        self.fields['role'].widget = forms.HiddenInput()

class CustomUserCreationForm(RoleMixin,FormStyleMixin, PasswordHandlingMixin, forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=True
    )
    
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        required=True
    )
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_css_classes()
        self.fields['email'].widget.input_type = 'email'
        self.setup_password_fields()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role',
                  'phone_number', 'password1', 'password2', 'profile_picture']

        def clean_role(self):
            role = self.cleaned_data.get('role')
            valid_roles = dict(User.USER_ROLES).keys()
            if role not in valid_roles:
                raise ValidationError(_('Invalid role selected'))
            return role

        def clean_phone_number(self):
            phone = self.cleaned_data.get('phone_number')
            if phone and not phone.startswith('+'):
                raise ValidationError(_('Phone number must start with "+" (e.g., +1234567890)'))
            return phone

class StudentCreationForm(CustomUserCreationForm):
    grade_level = forms.ModelChoiceField(
        queryset=Grade.objects.all(),
        required=True,
        empty_label=_('Select a Grade'),
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-md shadow-sm'}),
        help_text=_('Select the student\'s grade level')
    )
    
    parents = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='parent', is_active=True),  # Changed to User queryset
        required=False,
        widget=SearchableUserSelectWidget(field_type='parents'),  # Pass field_type
        help_text=_('Select parent(s) if already registered')
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role',
                  'phone_number', 'password1', 'password2', 'profile_picture']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_role('student')
        self.setup_password_fields()
        
        if self.instance and self.instance.pk:
            self.fields['grade_level'].required = False
            
            for field in ['password1', 'password2']:
                self.fields[field].required = False
                self.fields[field].widget.attrs['placeholder'] = 'Leave blank if not changing password'
            
            try:
                student_profile = self.instance.student_profile
                if student_profile.grade_level:
                    self.initial['grade_level'] = student_profile.grade_level
                
                # Get the User objects associated with the parents
                parent_users = [parent.user for parent in student_profile.parents.all()]
                self.initial['parents'] = parent_users
                
                # Debugging to verify parent data is loaded properly
                print(f"Initial parent users loaded: {len(parent_users)}")
                for parent in parent_users:
                    print(f"  Parent: {parent.get_full_name()} (ID: {parent.pk})")
                    
            except StudentProfile.DoesNotExist:
                pass
    
    def clean_grade_level(self):
        grade = self.cleaned_data.get('grade_level')
        
        if self.instance and self.instance.pk and not grade:
            try:
                grade = self.instance.student_profile.grade_level
                if grade:
                    return grade
            except (StudentProfile.DoesNotExist, AttributeError):
                pass
        
        if not grade and not self.instance.pk:
            raise ValidationError(_('Please select a valid grade level'))
        
        return grade
    
    def clean_parents(self):
        """
        Convert the list of User objects to ParentProfile objects.
        This runs after widget.value_from_datadict() returns user IDs
        """
        parent_user_ids = self.cleaned_data.get('parents')
        
        if not parent_user_ids:
            # Check if there are existing parents for this student
            if self.instance and hasattr(self.instance, 'student_profile'):
                try:
                    existing_parents = list(self.instance.student_profile.parents.all())
                    if existing_parents:
                        print(f"Found {len(existing_parents)} existing parents")
                        return existing_parents
                except Exception as e:
                    print(f"Error getting existing parents: {e}")
            return []
        
        print(f"Processing {len(parent_user_ids)} parent user IDs: {parent_user_ids}")
        
        # Get User objects from IDs
        parent_users = []
        if isinstance(parent_user_ids[0], int):  # If we have user IDs
            parent_users = User.objects.filter(id__in=parent_user_ids, role='parent')
        else:  # If we already have User objects
            parent_users = parent_user_ids
            
        # Convert User objects to ParentProfile objects
        parent_profiles = []
        for user in parent_users:
            try:
                parent_profile = ParentProfile.objects.get(user=user)
                parent_profiles.append(parent_profile)
                print(f"Added parent profile for {user.get_full_name()} (ID: {user.pk})")
            except ParentProfile.DoesNotExist:
                print(f"No parent profile found for user {user.pk}")
                pass
        
        # If editing an existing student, merge with existing parents that weren't removed
        if self.instance and hasattr(self.instance, 'student_profile'):
            try:
                existing_parent_ids = set(p.user.id for p in self.instance.student_profile.parents.all())
                submitted_parent_ids = set(u.id for u in parent_users)
                
                # Keep parents that weren't in the form submission (they should be retained)
                for parent_id in existing_parent_ids:
                    if parent_id not in submitted_parent_ids:
                        # This parent was in the database but not in the form submission
                        # Check if they were explicitly removed via the widget
                        removed_explicitly = (parent_id not in [int(id) for id in self.data.getlist(self.add_prefix('parents'))])
                        
                        if not removed_explicitly:
                            try:
                                user = User.objects.get(id=parent_id)
                                parent_profile = ParentProfile.objects.get(user=user)
                                if parent_profile not in parent_profiles:
                                    parent_profiles.append(parent_profile)
                                    print(f"Retained existing parent: {user.get_full_name()} (ID: {user.pk})")
                            except (User.DoesNotExist, ParentProfile.DoesNotExist):
                                pass
            except Exception as e:
                print(f"Error merging parents: {e}")
                
        print(f"Final parent profiles count: {len(parent_profiles)}")
        return parent_profiles
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        password = self.cleaned_data.get("password1")
        
        if password:
            user.set_password(password)
        elif user.pk:
            existing = User.objects.get(pk=user.pk)
            user.password = existing.password
        
        if commit:
            user.save()
            student_profile, _ = StudentProfile.objects.get_or_create(user=user)
            
            grade_level = self.cleaned_data.get('grade_level')
            if grade_level:
                student_profile.grade_level = grade_level
            
            student_profile.save()
            
            # Set parent profiles - this replaces existing relationships
            parent_profiles = self.cleaned_data.get('parents', [])
            if parent_profiles:
                print(f"Setting {len(parent_profiles)} parent profiles")
                for profile in parent_profiles:
                    if hasattr(profile, 'user'):
                        print(f"  - {profile.user.get_full_name()} (ID: {profile.user.pk})")
                student_profile.parents.set(parent_profiles)
            else:
                print("No parent profiles to set")
        
        return user

class AdminCreationForm(CustomUserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 
                'phone_number', 'password1', 'password2', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_role('admin')

class TeacherCreationForm(CustomUserCreationForm):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        help_text=_('Select the subjects this teacher will teach')
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 
                'phone_number', 'password1', 'password2', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_role('teacher')
        self.fields['subjects'].error_messages = {
            'required': _('Please select at least one subject')
        }
        
        # Pre-fill subjects if available when editing
        if self.instance and self.instance.pk:
            try:
                teacher_profile = self.instance.teacher_profile
                self.initial['subjects'] = teacher_profile.subjects.all()
            except TeacherProfile.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            teacher_profile, _ = TeacherProfile.objects.get_or_create(user=user)
            teacher_profile.subjects.set(self.cleaned_data['subjects'])

        return user

class ParentCreationForm(CustomUserCreationForm):
    children = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.all(),
        required=False,
        widget=SearchableUserSelectWidget,
        help_text=_('Select children if they are already registered')
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 
                'phone_number', 'password1', 'password2', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_role('parent')
        self.fields['children'].queryset = StudentProfile.objects.filter(
            user__is_active=True
        )
        
        # Pre-fill children if available when editing
        if self.instance and self.instance.pk:
            try:
                parent_profile = self.instance.parent_profile
                self.initial['children'] = parent_profile.children.all()
            except ParentProfile.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            parent_profile, _ = ParentProfile.objects.get_or_create(user=user)
            if self.cleaned_data.get('children'):
                parent_profile.children.set(self.cleaned_data['children'])

        return user

class StudentSignupForm(forms.ModelForm):
    """Standalone form for student self-registration."""

    first_name = forms.CharField(
        max_length=30,
        label='First Name',
        widget=forms.TextInput(attrs={'placeholder': 'First Name'})
    )

    last_name = forms.CharField(
        max_length=30,
        label='Last Name',
        widget=forms.TextInput(attrs={'placeholder': 'Last Name'})
    )

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )

    password1 = forms.CharField(
        label='Choose a password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Choose a password'}),
        validators=[MinLengthValidator(8)],
        help_text=_('Password must be at least 8 characters.')
    )

    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'})
    )

    grade_level = forms.ModelChoiceField(
        queryset=Grade.objects.all(),
        required=True,
        label='Grade Level',
        empty_label='Select a Grade',
        widget=forms.Select(attrs={'placeholder': 'Select a Grade'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'grade_level','password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("This email address is already taken."))
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        validate_password(password) 
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Passwords do not match."))

        return cleaned_data

    def save(self, commit=True):
        user = User(
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data['email'],
            role='student'  # explicitly set role
        )
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                grade_level=self.cleaned_data['grade_level']
            )
            print('saved')

        return user
    
class StudentLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email', 
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )
    password = forms.CharField( 
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )