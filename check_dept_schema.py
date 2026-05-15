from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE name='students_department'")
print(cursor.fetchone()[0])
