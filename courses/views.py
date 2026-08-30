from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.db.models import Q
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

# 課程列表（支援關鍵字搜尋 + 依老師篩選）
def course_list(request):
    courses = Course.objects.all().prefetch_related('teachers')

    search = request.GET.get('search', '').strip()
    teacher_param = request.GET.get('teacher', '').strip()

    # 把老師 id 轉成整數（轉換失敗或空值就當作沒有篩選）
    selected_teacher_id = None
    if teacher_param.isdigit():
        selected_teacher_id = int(teacher_param)

    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(teachers__name__icontains=search)
        ).distinct()

    if selected_teacher_id:
        courses = courses.filter(teachers__id=selected_teacher_id)

    # 事先算好每個老師是否為目前選中的老師，
    # 模板裡就不用寫比較運算子，避免編輯器格式化把 == 兩側空白吃掉造成語法錯誤
    teachers_for_filter = [
        {
            'id': teacher.id,
            'name': teacher.name,
            'selected': (teacher.id == selected_teacher_id),
        }
        for teacher in Teacher.objects.all()
    ]

    return render(request, 'courses/course_list.html', {
        'courses': courses,
        'teachers_for_filter': teachers_for_filter,
        'search': search,
        'selected_teacher_id': selected_teacher_id,
    })

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
    """
    老師列表：GET 公開，POST（新增老師）僅限管理員
    """
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class StudentListCreateView(generics.ListCreateAPIView):
    """
    學生列表：GET / POST 皆公開（依 README 規格，學生可自行報名系統時自行註冊）
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class CourseListView(generics.ListAPIView):
    """
    課程列表，支援：
    - ?search=關鍵字   （比對課程標題、說明、授課老師姓名）
    - ?teacher=老師id  （只顯示該老師教授的課程）
    可同時使用，例如 /api/courses/?search=英文&teacher=1
    """
    serializer_class = CourseSerializer

    def get_queryset(self):
        queryset = Course.objects.all().prefetch_related('teachers')

        search = self.request.query_params.get('search')
        teacher_id = self.request.query_params.get('teacher')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(teachers__name__icontains=search)
            ).distinct()

        if teacher_id:
            queryset = queryset.filter(teachers__id=teacher_id)

        return queryset


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