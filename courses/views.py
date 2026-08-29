from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Teacher, Student, Course, Enrollment
from .serializers import (
    TeacherSerializer, StudentSerializer, CourseSerializer,
    CourseCreateSerializer, EnrollmentSerializer, EnrollmentCreateSerializer
)

# -----------------------------
# 前端 Template Views
# -----------------------------

# 首頁
def home(request):
    return render(request, 'home.html')

# 課程列表
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})

# 課程詳情
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    students = Student.objects.all()
    enrollments = Enrollment.objects.filter(course=course).select_related('student')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        try:
            student = Student.objects.get(id=student_id)
            enrollment, created = Enrollment.objects.get_or_create(
                student=student,
                course=course
            )
            if created:
                messages.success(request, f'{student.name} 成功報名 {course.title}')
            else:
                messages.warning(request, f'{student.name} 已經報名過 {course.title}')
        except Student.DoesNotExist:
            messages.error(request, '學生不存在')
        except Exception as e:
            messages.error(request, f'報名失敗：{str(e)}')
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'students': students,
        'enrollments': enrollments
    })

# 老師列表
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'courses/teacher_list.html', {'teachers': teachers})

# 學生列表
def student_list(request):
    students = Student.objects.all()
    return render(request, 'courses/student_list.html', {'students': students})


# -----------------------------
# API Views
# -----------------------------

class TeacherListCreateView(generics.ListCreateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer


class StudentListCreateView(generics.ListCreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class CourseListView(generics.ListAPIView):
    queryset = Course.objects.all().prefetch_related('teachers')
    serializer_class = CourseSerializer


class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all().prefetch_related('teachers')
    serializer_class = CourseSerializer


class CourseCreateView(generics.CreateAPIView):
    """新增課程：只有管理員（is_staff=True）能操作"""
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [permissions.IsAdminUser]


class CourseDeleteView(generics.DestroyAPIView):
    """刪除課程：只有管理員（is_staff=True）能操作"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAdminUser]


@api_view(['POST'])
def enroll_student(request):
    serializer = EnrollmentCreateSerializer(data=request.data)
    if serializer.is_valid():
        enrollment = serializer.save()
        return Response({
            'message': '報名成功',
            'enrollment_id': enrollment.id,
            'student': enrollment.student.name,
            'course': enrollment.course.title
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)