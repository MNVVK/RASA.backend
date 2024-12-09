from django.db import models
from django.contrib.auth.models import User

class Engine(models.Model):
    title = models.CharField(max_length=400)
    description = models.TextField(null=True, blank=True)
    engine_data = models.CharField(max_length=400, null=True, blank=True)
    image_url = models.CharField(max_length=400, null=True, blank=True)
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('deleted', 'Удалён'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.title


class Acceptance(models.Model):
    title = models.CharField(max_length=400, null=True, blank=True)
    name = models.CharField(max_length=400, null=True, blank=True)
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('deleted', 'Удалён'),
        ('formed', 'Сформирован'),
        ('completed', 'Завершён'),
        ('rejected', 'Отклонён'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='acceptances')
    formation_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                                  blank=True,
                                  related_name='moderated_acceptances')

    class Meta:
        db_table = 'acceptance'

    def __str__(self):
        return f'Приёмка {self.id}'


class EngineAcceptance(models.Model):
    engine = models.ForeignKey(Engine, on_delete=models.CASCADE)
    acceptance = models.ForeignKey(Acceptance, on_delete=models.CASCADE)
    ACCEPTED_CHOICES = [
        ('accepted', 'Принято'),
        ('rejected', 'Не принято')
    ]
    accepted = models.CharField(max_length=20, choices=ACCEPTED_CHOICES, default='accepted')

    class Meta:
        unique_together = ['engine', 'acceptance']

    def __str__(self):
        return f"{self.acceptance} ({self.engine}): {self.accepted}"
