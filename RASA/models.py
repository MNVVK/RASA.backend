from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.db import models


class NewUserManager(UserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('User must have a username')

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(unique=True,
                                verbose_name="Имя пользователя")
    password = models.CharField(verbose_name="Пароль")
    is_staff = models.BooleanField(default=False,
                                   verbose_name="Модератор")
    is_superuser = models.BooleanField(default=False,
                                       verbose_name="Админ")

    USERNAME_FIELD = 'username'

    objects = NewUserManager()


class Engine(models.Model):
    title = models.CharField(max_length=400)
    description = models.TextField(null=True, blank=True)
    engine_data = models.CharField(max_length=400, null=True, blank=True)
    image_url = models.CharField(max_length=400, null=True, blank=True)
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('deleted', 'Удалён'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='active')

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
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                related_name='acceptances')
    formation_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    moderator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True,
                                  blank=True,
                                  related_name='moderated_acceptances')
    total_accepted = models.IntegerField(null=True, blank=True)

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
    accepted = models.CharField(max_length=20, choices=ACCEPTED_CHOICES,
                                default='accepted')

    class Meta:
        unique_together = ['engine', 'acceptance']

    def __str__(self):
        return f"{self.acceptance} ({self.engine}): {self.accepted}"
