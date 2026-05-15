from students.models import Department, AcademicYear
print(f"Depts: {list(Department.objects.values('id', 'name'))}")
print(f"Years: {list(AcademicYear.objects.values('id', 'year'))}")
