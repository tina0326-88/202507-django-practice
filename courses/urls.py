from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.course_list, name='course-list'),
    path('courses/<int:pk>/', views.course_detail, name='course-detail'),
    path('teachers/', views.teacher_list, name='teacher-list'),
    path('students/', views.student_list, name='student-list'),
]