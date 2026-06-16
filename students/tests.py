from django.test import TestCase
from students.forms import StudentForm
from students.models import Student, Department, AcademicYear
from core.models import DynamicChoice
from students.views import clean_and_validate_row, normalize_department, normalize_academic_year, split_arabic_name

class StudentFormChoiceTests(TestCase):
    def test_choices_present_in_form(self):
        form = StudentForm()
        # Verify birth_place choices match the expected options
        birth_place_choices = form.fields['birth_place'].choices
        # Choices tuple list contains a blank default (like '---------') plus the choices
        choices_only = [c[0] for c in birth_place_choices if c[0]]
        
        self.assertIn('بغداد', choices_only)
        self.assertIn('البصرة', choices_only)
        self.assertIn('خارج العراق', choices_only)

        # Verify citizenship choices
        citizenship_choices = form.fields['citizenship'].choices
        citizenship_only = [c[0] for c in citizenship_choices if c[0]]
        self.assertListEqual(citizenship_only, ['عراقي', 'أجنبي'])

    def test_dynamic_choices_override(self):
        # Create a new dynamic choice (appended)
        DynamicChoice.objects.create(category='birth_place', value='كربلاء', display_name='كربلاء')
        # Override and rename a default choice
        DynamicChoice.objects.create(category='citizenship', value='عراقي', display_name='عراقي معدل')
        # Disable a default choice
        DynamicChoice.objects.create(category='citizenship', value='أجنبي', is_active=False)

        form = StudentForm()

        # Check that birth_place contains BOTH default and new custom choices
        birth_place_choices = form.fields['birth_place'].choices
        choices_only = [c[0] for c in birth_place_choices if c[0]]
        self.assertIn('كربلاء', choices_only)
        self.assertIn('بغداد', choices_only)  # Defaults should NOT be lost when adding new ones

        # Check citizenship
        citizenship_choices = form.fields['citizenship'].choices
        citizenship_only = [c[0] for c in citizenship_choices if c[0]]
        self.assertIn('عراقي', citizenship_only)  # Still exists
        self.assertEqual(dict(citizenship_choices).get('عراقي'), 'عراقي معدل')  # But renamed!
        self.assertNotIn('أجنبي', citizenship_only)  # Disabled/hidden successfully!

    def test_form_validation_valid_choices(self):
        form_data = {
            'first_name': 'أحمد',
            'second_name': 'علي',
            'third_name': 'حسين',
            'national_id': '123456789012',
            'date_of_birth': '2000-01-01',
            'gender': 'male',
            'birth_place': 'بغداد',
            'citizenship': 'عراقي',
        }
        form = StudentForm(data=form_data)
        form.is_valid()
        self.assertNotIn('birth_place', form.errors)
        self.assertNotIn('citizenship', form.errors)

    def test_form_validation_invalid_choices(self):
        form_data = {
            'birth_place': 'مدينة مجهولة',
            'citizenship': 'فرنسي',
        }
        form = StudentForm(data=form_data)
        form.is_valid()
        self.assertIn('birth_place', form.errors)
        self.assertIn('citizenship', form.errors)


class ImportCleaningEngineTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="قسم هندسة البرمجيات", code="SWE")
        self.year = AcademicYear.objects.create(year="2024/2025", start_date="2024-09-01", end_date="2025-06-30")

    def test_normalize_department(self):
        # Exact match
        self.assertEqual(normalize_department("قسم هندسة البرمجيات"), self.dept)
        # Fuzzy match (substring)
        self.assertEqual(normalize_department("البرمجيات"), self.dept)
        # Non-matching
        self.assertIsNone(normalize_department("قسم الطب البشري"))

    def test_normalize_academic_year(self):
        # Exact match
        self.assertEqual(normalize_academic_year("2024/2025"), self.year)
        # Year digit match
        self.assertEqual(normalize_academic_year("2024"), self.year)
        # Non-matching
        self.assertIsNone(normalize_academic_year("2018"))

    def test_clean_and_validate_row_gender(self):
        # Test male
        row_male = {'gender': 'ذكر', 'national_id': '111111111111', 'first_name': 'أحمد', 'second_name': 'علي', 'third_name': 'حسين'}
        cleaned, errors = clean_and_validate_row(row_male, 1)
        self.assertEqual(cleaned['gender'], 'male')
        self.assertEqual(len(errors), 0)

        # Test female
        row_female = {'gender': 'بنت', 'national_id': '222222222222', 'first_name': 'فاطمة', 'second_name': 'علي', 'third_name': 'حسين'}
        cleaned, errors = clean_and_validate_row(row_female, 2)
        self.assertEqual(cleaned['gender'], 'female')

        # Test invalid gender
        row_invalid = {'gender': 'غير محدد', 'national_id': '333333333333', 'first_name': 'شخص', 'second_name': 'علي', 'third_name': 'حسين'}
        cleaned, errors = clean_and_validate_row(row_invalid, 3)
        self.assertTrue(any("الجنس غير صالح" in e for e in errors))

    def test_clean_and_validate_row_citizenship(self):
        # Test iraqi
        row_iraqi = {'citizenship': 'عراقية', 'national_id': '111111111111', 'first_name': 'أحمد', 'second_name': 'علي', 'third_name': 'حسين'}
        cleaned, errors = clean_and_validate_row(row_iraqi, 1)
        self.assertEqual(cleaned['citizenship'], 'عراقي')

        # Test foreign
        row_foreign = {'citizenship': 'اجنبي', 'national_id': '111111111111', 'first_name': 'أحمد', 'second_name': 'علي', 'third_name': 'حسين'}
        cleaned, errors = clean_and_validate_row(row_foreign, 1)
        self.assertEqual(cleaned['citizenship'], 'أجنبي')

    def test_clean_and_validate_row_phone(self):
        row_phone = {'phone': '0770-123-4567', 'national_id': '111111111111', 'first_name': 'أحمد', 'second_name': 'علي', 'third_name': 'حسين'}
        cleaned, errors = clean_and_validate_row(row_phone, 1)
        self.assertEqual(cleaned['phone'], '07701234567')

    def test_clean_and_validate_row_validation_errors(self):
        # Missing required name
        row_missing_name = {'national_id': '111111111111', 'first_name': '', 'second_name': 'علي', 'third_name': 'حسين'}
        cleaned, errors = clean_and_validate_row(row_missing_name, 1)
        self.assertTrue(any("الاسم الأول حقل مطلوب" in e for e in errors))

        # Missing national ID
        row_missing_nat = {'national_id': '', 'first_name': 'أحمد', 'second_name': 'علي', 'third_name': 'حسين'}
        cleaned, errors = clean_and_validate_row(row_missing_nat, 2)
        self.assertTrue(any("رقم الهوية/الجواز حقل مطلوب" in e for e in errors))

    def test_student_import_export_view_restricted(self):
        from django.contrib.auth.models import User
        from django.urls import reverse
        staff_user = User.objects.create_user(username="staff_import", password="password", is_staff=True)
        superuser = User.objects.create_superuser(username="superuser_import", password="password")
        
        url = reverse('student_import_export')
        
        self.client.login(username="staff_import", password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        self.client.login(username="superuser_import", password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_split_arabic_name_helper(self):
        # Simple names
        self.assertEqual(split_arabic_name("أحمد علي حسين"), ["أحمد", "علي", "حسين"])
        
        # Compound names
        self.assertEqual(split_arabic_name("عبد الرضا محمد علي"), ["عبد الرضا", "محمد", "علي"])
        self.assertEqual(split_arabic_name("زين العابدين عبد الرضا محمد علي عبيد"), ["زين العابدين", "عبد الرضا", "محمد", "علي", "عبيد"])
        self.assertEqual(split_arabic_name("محمد باقر علي حسين"), ["محمد باقر", "علي", "حسين"])
        self.assertEqual(split_arabic_name("علاء الدين سيف الله محمد"), ["علاء الدين", "سيف الله", "محمد"])

    def test_clean_and_validate_row_arabic_name_splitting(self):
        # زهراء عبد الرضا محمد علي
        row1 = {
            'national_id': '200594915066',
            'first_name': 'زهراء عبد الرضا محمد علي',
            'second_name': '',
            'third_name': '',
        }
        cleaned1, errors1 = clean_and_validate_row(row1, 1)
        self.assertEqual(errors1, [])
        self.assertEqual(cleaned1['first_name'], 'زهراء')
        self.assertEqual(cleaned1['second_name'], 'عبد الرضا')
        self.assertEqual(cleaned1['third_name'], 'محمد')
        self.assertEqual(cleaned1['last_name'], 'علي')

        # عقيل شاهر داود زاهي
        row2 = {
            'national_id': '200286975301',
            'first_name': 'عقيل شاهر داود زاهي',
            'second_name': '',
            'third_name': '',
        }
        cleaned2, errors2 = clean_and_validate_row(row2, 2)
        self.assertEqual(errors2, [])
        self.assertEqual(cleaned2['first_name'], 'عقيل')
        self.assertEqual(cleaned2['second_name'], 'شاهر')
        self.assertEqual(cleaned2['third_name'], 'داود')
        self.assertEqual(cleaned2['last_name'], 'زاهي')

        # رقية عادل حسن شراد
        row3 = {
            'national_id': '200466015174',
            'first_name': 'رقية عادل حسن شراد',
            'second_name': None,
            'third_name': None,
        }
        cleaned3, errors3 = clean_and_validate_row(row3, 3)
        self.assertEqual(errors3, [])
        self.assertEqual(cleaned3['first_name'], 'رقية')
        self.assertEqual(cleaned3['second_name'], 'عادل')
        self.assertEqual(cleaned3['third_name'], 'حسن')
        self.assertEqual(cleaned3['last_name'], 'شراد')

    def test_cleanup_import_temp_files_only_deletes_session_files(self):
        import os
        from django.conf import settings
        from students.views import cleanup_import_temp_files
        
        # Create temp_imports directory for testing if not exists
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'test_temp_imports')
        os.makedirs(temp_dir, exist_ok=True)
        
        session_file_path = os.path.join(temp_dir, 'session_file.xlsx')
        other_file_path = os.path.join(temp_dir, 'other_user_file.xlsx')
        
        try:
            # Create session file
            with open(session_file_path, 'w') as f:
                f.write('session data')
                
            # Create other user's file
            with open(other_file_path, 'w') as f:
                f.write('other data')
                
            # Mock request and session
            class MockSession(dict):
                pass
            class MockRequest:
                def __init__(self):
                    self.session = MockSession()
            
            request = MockRequest()
            request.session['import_temp_file'] = 'session_file.xlsx'
            
            # Run cleanup
            cleanup_import_temp_files(request, temp_dir)
            
            # Verify session file was deleted
            self.assertFalse(os.path.exists(session_file_path))
            # Verify other file was NOT deleted (cross-session protection!)
            self.assertTrue(os.path.exists(other_file_path))
            
        finally:
            # Clean up test files
            if os.path.exists(session_file_path):
                os.remove(session_file_path)
            if os.path.exists(other_file_path):
                os.remove(other_file_path)
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)

    def test_column_header_synonym_matching(self):
        from django.contrib.auth.models import User
        from django.urls import reverse
        import io
        import tablib
        
        superuser = User.objects.create_superuser(username="super_synonym", password="password")
        self.client.login(username="super_synonym", password="password")
        
        # Create a CSV dataset with custom headers
        dataset = tablib.Dataset()
        dataset.headers = ['اسم الطالب', 'رقم الهوية', 'الهاتف']
        dataset.append(['زهراء عبد الرضا محمد علي', '200594915066', '07701234567'])
        
        # Convert to bytes
        csv_file = io.BytesIO(dataset.csv.encode('utf-8-sig'))
        csv_file.name = 'test_import.csv'
        
        url = reverse('student_import_export')
        
        # Step 1: Upload
        response = self.client.post(url, {
            'action': 'import_upload',
            'import_file': csv_file
        })
        
        # Check that we succeeded and moved to step 2
        self.assertEqual(response.status_code, 200)
        self.assertIn('step', response.context)
        self.assertEqual(response.context['step'], 2)
        
        # Verify that session matches are populated using synonyms
        matches = self.client.session.get('import_column_matches')
        self.assertIsNotNone(matches)
        self.assertEqual(matches.get('اسم الطالب'), 'first_name')
        self.assertEqual(matches.get('رقم الهوية'), 'national_id')
        self.assertEqual(matches.get('الهاتف'), 'phone')

    def test_auto_create_department_and_academic_year(self):
        # Verify that if we run clean_and_validate_row on a non-existent department or academic year,
        # it automatically creates them and registers them in the database.
        row = {
            'national_id': '200351079396',
            'first_name': 'اطياف فاضل شناوه سعدون',
            'second_name': '',
            'third_name': '',
            'department': 'قسم تربية كيمياء',
            'entry_year': '2025/2026',
        }
        
        # Check that they don't exist yet
        self.assertFalse(Department.objects.filter(name='قسم تربية كيمياء').exists())
        self.assertFalse(AcademicYear.objects.filter(year='2025/2026').exists())
        
        # Clean and validate row (which calls helpers with auto_create=True)
        cleaned, errors = clean_and_validate_row(row, 1)
        
        # Verify no errors are thrown for missing department/year
        self.assertEqual(errors, [])
        
        # Verify they were created in DB
        self.assertTrue(Department.objects.filter(name='قسم تربية كيمياء').exists())
        self.assertTrue(AcademicYear.objects.filter(year='2025/2026').exists())
        
        # Verify clean_and_validate_row resolved them
        dept = Department.objects.get(name='قسم تربية كيمياء')
        year = AcademicYear.objects.get(year='2025/2026')
        self.assertEqual(cleaned['department'], 'قسم تربية كيمياء')
        self.assertEqual(cleaned['entry_year'], '2025/2026')




