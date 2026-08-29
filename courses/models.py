from django.db import models

class Teacher(models.Model):
    name = models.CharField(max_length=100, verbose_name="老師姓名")
    email = models.EmailField(unique=True, verbose_name="電子信箱")
    bio = models.TextField(blank=True, null=True, verbose_name="老師介紹")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "老師"
        verbose_name_plural = "老師"


class Student(models.Model):
    LEVEL_CHOICES = [
        ("beginner", "初級"),
        ("intermediate", "中級"),
        ("advanced", "高級"),
    ]

    name = models.CharField(max_length=100, verbose_name="學生姓名")
    email = models.EmailField(unique=True, verbose_name="電子信箱")
    level = models.CharField(
        max_length=20, choices=LEVEL_CHOICES, default="beginner", verbose_name="程度"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "學生"
        verbose_name_plural = "學生"


class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="課程名稱")
    description = models.TextField(blank=True, verbose_name="課程說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    # 多對多：一門課可以有多位老師，一位老師可以教多門課
    teachers = models.ManyToManyField(
        Teacher, related_name="courses", blank=True, verbose_name="授課老師"
    )

    # 透過 Enrollment 中介表建立學生的多對多關係
    students = models.ManyToManyField(
        Student, through="Enrollment", related_name="courses", verbose_name="報名學生"
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "課程"
        verbose_name_plural = "課程"
        ordering = ["-created_at"]


class Enrollment(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="enrollments", verbose_name="學生"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments", verbose_name="課程"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="報名時間")

    class Meta:
        # 關鍵：確保同一學生對同一課程只能報名一次
        unique_together = ("student", "course")
        verbose_name = "報名紀錄"
        verbose_name_plural = "報名紀錄"
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student.name} → {self.course.title}"