from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.ulogout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('test/', views.test, name='test'),

    path('user/<str:role>/create/', views.role_ops, name='create_user'),
    path('user/<str:role>/<int:uid>/edit/', views.role_ops, name='edit_user'),

    # path('add_role/<str:role>/', views.add_role, name='add_role'),
    path('role_results/', views.role_results, name='role_results'),
    path('api/users/search/', views.search_users, name='search_users'),
]
