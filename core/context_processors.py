from .models import SystemSettings

def system_settings(request):
    settings = SystemSettings.objects.first()
    if not settings:
        # Provide default values if no settings exist yet
        settings = {
            'university_name': "الجامعة التقنية",
            'college_name': "",
            'header_color': "#1a237e",
        }
    return {'sys_settings': settings}
