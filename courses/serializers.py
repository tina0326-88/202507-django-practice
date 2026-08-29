from rest_framework import serializers
from .models import Teacher, Student, Course, Enrollment


class TeacherSerializer(serializers.ModelSerializer):
    course_count = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ["id", "name", "email", "bio", "course_count"]

    def get_course_count(self, obj):
        return obj.courses.count()


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "name", "email", "level"]


class TeacherBriefSerializer(serializers.ModelSerializer):
    """課程詳情裡用來簡短顯示老師資訊，避免巢狀太深"""
    class Meta:
        model = Teacher
        fields = ["id", "name", "email"]


class CourseSerializer(serializers.ModelSerializer):
    # 寫入時：接受老師 id 陣列
    teachers = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), many=True, required=False
    )
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "teachers",
            "student_count",
        ]
        read_only_fields = ["created_at"]

    def get_student_count(self, obj):
        return obj.students.count()

    def to_representation(self, instance):
        """
        讀取時：把 teachers 從純 id 列表換成簡短物件（id/name/email），
        這樣前端不用再多打一次 API 查老師名字。
        """
        rep = super().to_representation(instance)
        rep["teachers"] = TeacherBriefSerializer(instance.teachers.all(), many=True).data
        return rep


class CourseBriefSerializer(serializers.ModelSerializer):
    """報名紀錄裡用來簡短顯示課程資訊"""
    class Meta:
        model = Course
        fields = ["id", "title"]


class CourseCreateSerializer(serializers.ModelSerializer):
    """新增課程專用：接受 teachers 為 id 陣列"""
    teachers = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), many=True, required=False
    )

    class Meta:
        model = Course
        fields = ["id", "title", "description", "created_at", "teachers"]
        read_only_fields = ["id", "created_at"]


class EnrollmentSerializer(serializers.ModelSerializer):
    # 對外的欄位名稱維持 student_id / course_id
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), source="course"
    )

    class Meta:
        model = Enrollment
        fields = ["id", "student_id", "course_id", "enrolled_at"]
        read_only_fields = ["enrolled_at"]
        validators = []  # 停用自動產生的 UniqueTogetherValidator，改用下面 validate() 自訂錯誤訊息

    def validate(self, attrs):
        student = attrs.get("student")
        course = attrs.get("course")
        if Enrollment.objects.filter(student=student, course=course).exists():
            raise serializers.ValidationError(
                {"detail": "此學生已報名過此課程"}
            )
        return attrs

    def to_representation(self, instance):
        """
        讀取時：course_id 保持數字 id 即可（符合 README 格式），
        如果之後前端想要更豐富的資訊，可以額外加一個 course 欄位。
        """
        rep = super().to_representation(instance)
        rep["student_id"] = instance.student_id
        rep["course_id"] = instance.course_id
        return rep


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """報名專用：對外欄位名稱為 student_id / course_id"""
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), source="course"
    )

    class Meta:
        model = Enrollment
        fields = ["student_id", "course_id"]
        validators = []  # 停用自動產生的 UniqueTogetherValidator，改用下面 validate() 自訂錯誤訊息

    def validate(self, attrs):
        student = attrs.get("student")
        course = attrs.get("course")
        if Enrollment.objects.filter(student=student, course=course).exists():
            raise serializers.ValidationError(
                {"detail": "此學生已報名過此課程"}
            )
        return attrs