from django.urls import path
from .views import *

app_name = 'exam'
urlpatterns = [
    path('create/', create, name='create_paper'),
    path('save/<int:exam_id>/', save_exam, name='save_exam'),

    path('create-paper/', save_exam, name='create_exam'),
    path('save_question/<int:exam_id>/', save_question, name='save_question'),
    path('exam_list/', exam_list, name='exam_list'),
    path('toggle-exam-active/<int:exam_id>/',toggle_exam_active, name='toggle_exam_active'),
    path('toggle-exam-shuffle/<int:exam_id>/', toggle_exam_shuffle, name='toggle_exam_shuffle'),
    
    path('question_info/<int:exam_id>/', question_info, name='question_info'),
    path('update_student_question_limit/<int:exam_id>/', update_student_question_limit, name='update_student_question_limit'),
    path('edit/<int:exam_id>/', edit, name='edit'),
    path('delete/<int:exam_id>/', delete, name='delete'),
    
    path('search/', exam_list, name='exam_search'),

    path('take/<int:exam_id>/', take_exam, name='take_exam'),
    path('submit/<int:attempt_id>/', submit_exam, name='submit_exam'),
    path('results/<int:attempt_id>/', exam_results, name='exam_results'),
    path('ping/<int:attempt_id>/', ping, name='ping'),
    path('active_papers/', active_papers, name='active_papers'),
    path('ready/<int:exam_id>/', exam_ready, name='ready'),
    path('results/', results, name='results'),
    
    path('get_folder_tree/', get_folder_structure, name='get_folder_tree'),
    path('folder/create/', folder_operations, name='create_folder'),
    path('folder/edit/<int:folder_id>/', folder_operations, name='edit_folder'),
    path('folder/delete/<int:folder_id>/', folder_operations, name='delete_folder'),

] 