from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import SystemLog

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    SystemLog.objects.create(
        user=user,
        action='login',
        details=f"قام المستخدم {user.username} بتسجيل الدخول."
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        SystemLog.objects.create(
            user=user,
            action='logout',
            details=f"قام المستخدم {user.username} بتسجيل الخروج."
        )

@receiver(post_save, sender=User)
def log_user_save(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'
    details_text = f"تم إنشاء مستخدم جديد: {instance.username}" if created else f"تم تعديل بيانات المستخدم: {instance.username}"
    SystemLog.objects.create(
        user=None, # Cannot easily get request.user here without middleware, but we record the action
        action=action,
        details=details_text
    )

@receiver(post_delete, sender=User)
def log_user_delete(sender, instance, **kwargs):
    SystemLog.objects.create(
        user=None,
        action='delete',
        details=f"تم حذف المستخدم: {instance.username}"
    )
