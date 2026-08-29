from django.contrib.auth.models import User
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Teacher, Student, Course, Enrollment


class ModelTests(TestCase):
    """測試 model 層的資料限制"""

    def setUp(self):
        self.teacher = Teacher.objects.create(
            name="王老師", email="teacher_wang@example.com", bio="英文老師"
        )
        self.student = Student.objects.create(
            name="小明", email="student_ming@example.com", level="beginner"
        )
        self.course = Course.objects.create(
            title="英文入門", description="基礎文法與聽力練習"
        )
        self.course.teachers.add(self.teacher)

    def test_course_str(self):
        self.assertEqual(str(self.course), "英文入門")

    def test_teacher_can_teach_multiple_courses(self):
        course2 = Course.objects.create(title="英文中級", description="進階文法")
        course2.teachers.add(self.teacher)
        self.assertEqual(self.teacher.courses.count(), 2)

    def test_enrollment_success(self):
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.assertEqual(self.course.students.count(), 1)
        self.assertEqual(enrollment.student, self.student)

    def test_duplicate_enrollment_raises_integrity_error(self):
        """同一學生對同一課程報名兩次，資料庫層級應該擋下來"""
        Enrollment.objects.create(student=self.student, course=self.course)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Enrollment.objects.create(student=self.student, course=self.course)


class TeacherAPITests(APITestCase):
    def setUp(self):
        self.teacher = Teacher.objects.create(
            name="王老師", email="teacher_wang@example.com", bio="英文老師"
        )

    def test_list_teachers(self):
        url = reverse("teacher-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_create_teacher(self):
        url = reverse("teacher-list-create")
        payload = {
            "name": "李老師",
            "email": "teacher_lee@example.com",
            "bio": "數學老師",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Teacher.objects.count(), 2)

    def test_create_teacher_duplicate_email_fails(self):
        url = reverse("teacher-list-create")
        payload = {
            "name": "重複信箱老師",
            "email": "teacher_wang@example.com",  # 跟 setUp 裡的老師撞信箱
            "bio": "",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CourseAPITests(APITestCase):
    def setUp(self):
        self.teacher = Teacher.objects.create(
            name="王老師", email="teacher_wang@example.com"
        )
        self.course = Course.objects.create(
            title="英文入門", description="基礎文法與聽力練習"
        )
        self.course.teachers.add(self.teacher)

    def test_list_courses(self):
        url = reverse("course-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_course_shows_teacher_detail(self):
        url = reverse("course-detail", kwargs={"pk": self.course.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # to_representation 應該把 teachers 展開成物件，而不是純 id
        self.assertEqual(response.data["teachers"][0]["name"], "王老師")

    def test_create_course_with_teachers(self):
        """管理員登入後才能新增課程"""
        admin = User.objects.create_user(
            username="admin", password="testpass123", is_staff=True
        )
        self.client.force_authenticate(user=admin)
        url = reverse("course-create")
        payload = {
            "title": "英文中級",
            "description": "進階文法練習",
            "teachers": [self.teacher.id],
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 2)

    def test_create_course_requires_admin(self):
        """未登入的一般訪客不能新增課程"""
        url = reverse("course-create")
        payload = {"title": "英文中級", "description": "進階文法練習"}
        response = self.client.post(url, payload, format="json")
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
        self.assertEqual(Course.objects.count(), 1)

    def test_delete_course_requires_admin(self):
        """未登入的一般訪客不能刪除課程"""
        url = reverse("course-delete", kwargs={"pk": self.course.pk})
        response = self.client.delete(url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())

    def test_delete_course_as_admin_succeeds(self):
        """管理員登入後可以刪除課程"""
        admin = User.objects.create_user(
            username="admin2", password="testpass123", is_staff=True
        )
        self.client.force_authenticate(user=admin)
        url = reverse("course-delete", kwargs={"pk": self.course.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Course.objects.filter(pk=self.course.pk).exists())


class EnrollmentAPITests(APITestCase):
    def setUp(self):
        self.student = Student.objects.create(
            name="小明", email="student_ming@example.com", level="beginner"
        )
        self.course = Course.objects.create(
            title="英文入門", description="基礎文法與聽力練習"
        )

    def test_enroll_success(self):
        url = reverse("enroll-student")
        payload = {"student_id": self.student.id, "course_id": self.course.id}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "報名成功")
        self.assertEqual(Enrollment.objects.count(), 1)

    def test_duplicate_enrollment_returns_400(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        url = reverse("enroll-student")
        payload = {"student_id": self.student.id, "course_id": self.course.id}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_enroll_with_nonexistent_student_fails(self):
        url = reverse("enroll-student")
        payload = {"student_id": 9999, "course_id": self.course.id}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)