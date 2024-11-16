from django.db import models


class Engine(models.Model):
    title = models.CharField(max_length=400)
    description = models.TextField()
    image_url = models.CharField(max_length=400)

    def __str__(self):
        return self.title


from django.contrib.auth.models import User


class Service(models.Model):
    name = models.CharField(max_length=255, default="Untitled")
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[('active', 'Действует'), ('deleted', 'Удален')], default="active")
    image_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class Application(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('deleted', 'Удалён'),
        ('formed', 'Сформирован'),
        ('completed', 'Завершён'),
        ('rejected', 'Отклонён'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='applications')
    formation_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    moderator = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name='moderated_applications')

    def __str__(self):
        return f"Application {self.id} - {self.status}"


class ApplicationService(models.Model):
    application = models.ForeignKey(Application, on_delete=models.PROTECT)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    is_main = models.BooleanField(default=False)

    class Meta:
        unique_together = ['application', 'service']

    def __str__(self):
        return f"{self.application} - {self.service}"

# Используется системная таблица User из Django, дополнительных моделей не требуется
