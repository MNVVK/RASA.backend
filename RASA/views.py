import os
import uuid
import mimetypes
from urllib.parse import urlparse

import boto3
import redis
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Engine, Acceptance, EngineAcceptance, Attribute, \
    EngineAttribute
from .permissions import IsModer
from .serializers import (
    EngineSerializer, AcceptanceSerializer,
    AcceptanceDetailSerializer, UserSerializer, EngineAcceptanceSerializer,
    AcceptanceStatusSerializer,
)
from .services.generate_qr import generate_acceptance_qr

User = get_user_model()

# session_storage = redis.StrictRedis(host=settings.REDIS_HOST,
#                                   port=settings.REDIS_PORT)

# Подключение к Redis через URL
session_storage = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True  # чтобы строки возвращались как str, а не bytes
)


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


class EngineListAPIView(APIView):
    def get(self, request):
        # Исключаем удалённые двигатели
        user = request.user

        engines = Engine.objects.all()

        if 'engine_title' in request.query_params:
            engine_title = request.query_params['engine_title']
            engines = engines.filter(title__icontains=engine_title)

        if user.is_authenticated:
            if not user.is_superuser:
                engines = engines.exclude(status='deleted')

            draft = Acceptance.objects.filter(creator=user,
                                              status='draft').first()
            draft_id = draft.id if draft else None
            draft_engines_count = EngineAcceptance.objects.filter(
                acceptance=draft).count() if draft else 0
        else:
            engines = engines.exclude(status='deleted')
            draft_id = None
            draft_engines_count = 0

        serializer = EngineSerializer(engines, many=True)

        response_data = {
            'draft_id': draft_id,
            'draft_engines_count': draft_engines_count,
            'engines': serializer.data
        }

        return Response(response_data)

    @swagger_auto_schema(request_body=EngineSerializer)
    @method_permission_classes((IsModer,))
    def post(self, request):
        serializer = EngineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EngineDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            engine = Engine.objects.get(pk=pk)
            serializer = EngineSerializer(engine)
            return Response(serializer.data)
        except Engine.DoesNotExist:
            return Response({'error': 'Двигатель не найден или удалён'},
                            status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=EngineSerializer)
    @method_permission_classes((IsModer,))
    def put(self, request, pk):
        try:
            engine = Engine.objects.get(pk=pk)

            serializer = EngineSerializer(engine, data=request.data,
                                          partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        except Engine.DoesNotExist:
            return Response({'error': 'Двигатель не найден или удалён'},
                            status=status.HTTP_404_NOT_FOUND)

    @method_permission_classes((IsModer,))
    def delete(self, request, pk):
        try:
            engine = Engine.objects.get(pk=pk)
            if engine.status == 'deleted':
                return Response({'error': 'Этот двигатель уже удалён'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Удаляем файл из S3, если был
            if engine.image_url:
                try:
                    s3_delete_by_url(engine.image_url)
                except Exception as e:
                    return Response({'error': f'Ошибка удаления из S3: {e}'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            engine.image_url = None
            engine.status = 'deleted'
            engine.save(update_fields=["image_url", "status"])

            return Response({'message': 'Двигатель успешно удалён'})
        except Engine.DoesNotExist:
            return Response({'error': 'Двигатель не найден или удалён'},
                            status=status.HTTP_404_NOT_FOUND)


# ---- S3 client (Yandex Object Storage) ----
s3_client = boto3.client(
    "s3",
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)


def s3_public_url(object_key: str) -> str:
    """Вернёт публичный URL объекта."""
    return f"{settings.AWS_PUBLIC_BASE_URL}/{object_key.lstrip('/')}"


def s3_upload_public(file_obj, object_key: str, content_type: str | None = None):
    """Загрузка в S3 с ACL=public-read."""
    extra = {"ACL": "public-read"}
    if content_type:
        extra["ContentType"] = content_type
    s3_client.upload_fileobj(
        Fileobj=file_obj,
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=object_key,
        ExtraArgs=extra,
    )


def s3_delete_by_url(url: str):
    """Удалит объект по публичному URL."""
    # ожидаем вид https://storage.yandexcloud.net/<bucket>/<key>
    parsed = urlparse(url)
    # путь начинается с /bucket/key...
    parts = parsed.path.lstrip("/").split("/", 1)
    if len(parts) != 2:
        return
    bucket, key = parts
    # на всякий случай верифицируем, что bucket совпадает с текущим
    if bucket != settings.AWS_STORAGE_BUCKET_NAME:
        # если хочешь — можно бросать исключение/логировать
        pass
    s3_client.delete_object(Bucket=bucket, Key=key)


from botocore.exceptions import ClientError, BotoCoreError


class EngineAddImageAPIView(APIView):
    @method_permission_classes((IsModer,))
    def post(self, request, pk):
        try:
            engine = Engine.objects.get(pk=pk)
        except Engine.DoesNotExist:
            return Response({'error': 'Двигатель не найден или удалён'},
                            status=status.HTTP_404_NOT_FOUND)

        file_obj = request.FILES.get('file') or request.FILES.get('image')
        if not file_obj:
            return Response({'error': "Файл не передан (ожидается поле 'file' или 'image')"},
                            status=status.HTTP_400_BAD_REQUEST)

        orig_name = file_obj.name or "upload.bin"
        _, ext = os.path.splitext(orig_name)
        ext = (ext or ".bin").lower()

        content_type = getattr(file_obj, "content_type", None) \
                       or mimetypes.guess_type(orig_name)[0] \
                       or "application/octet-stream"

        object_key = f"engines/{pk}/{uuid.uuid4().hex}{ext}"

        try:
            s3_upload_public(file_obj, object_key, content_type=content_type)
        except ClientError as e:
            # В ответ вернём точный код/сообщение от S3
            code = e.response.get("Error", {}).get("Code")
            msg = e.response.get("Error", {}).get("Message")
            print("S3 ClientError:", code, msg)  # в консоль Django
            return Response({'error': f'S3 ClientError: {code}: {msg}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except BotoCoreError as e:
            print("S3 BotoCoreError:", repr(e))
            return Response({'error': f'BotoCoreError: {e}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print("S3 unknown error:", repr(e))
            return Response({'error': f'Ошибка загрузки в S3: {e}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        image_url = s3_public_url(object_key)
        engine.image_url = image_url
        engine.save(update_fields=["image_url"])

        return Response({'message': 'Изображение успешно добавлено', 'url': image_url},
                        status=status.HTTP_200_OK)


class AddEngineToDraftAPIView(APIView):
    @method_permission_classes((IsAuthenticated,))
    def post(self, request, pk):
        try:
            engine = Engine.objects.get(pk=pk)

            # Проверка на статус удалённости двигателя
            if engine.status == 'deleted':
                return Response({
                    'error': 'Этот двигатель удалён и не может быть добавлен в черновик'},
                    status=status.HTTP_400_BAD_REQUEST)

            draft, created = Acceptance.objects.get_or_create(
                creator=request.user, status='draft',
            )
            if EngineAcceptance.objects.filter(engine=engine,
                                               acceptance=draft).exists():
                return Response({'error': 'Двигатель уже добавлен в черновик'},
                                status=status.HTTP_400_BAD_REQUEST)

            mm = EngineAcceptance.objects.create(engine=engine,
                                                 acceptance=draft)
            serializer = EngineAcceptanceSerializer(instance=mm)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Двигатель не найден'},
                            status=status.HTTP_404_NOT_FOUND)


class DraftEngineManagementAPIView(APIView):
    @method_permission_classes((IsAuthenticated,))
    def delete(self, request, pk):
        try:
            user = request.user
            draft = Acceptance.objects.filter(creator=user,
                                              status='draft').first()

            if not draft:
                return Response({'error': 'Черновик не найден'},
                                status=status.HTTP_404_NOT_FOUND)

            # Проверяем, есть ли связь с двигателем
            engine_acceptance = EngineAcceptance.objects.filter(
                engine_id=pk, acceptance=draft).first()

            if not engine_acceptance:
                return Response({'error': 'Двигатель не найден в черновике'},
                                status=status.HTTP_404_NOT_FOUND)

            # Удаляем связь
            engine_acceptance.delete()

            return Response(
                {'message': 'Двигатель успешно удалён из черновика'}, )
        except Exception as e:
            return Response({'error': f'Ошибка: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(request_body=EngineAcceptanceSerializer)
    @method_permission_classes((IsAuthenticated,))
    def put(self, request, pk):
        try:
            user = request.user
            draft = Acceptance.objects.filter(creator=user,
                                              status='draft').first()

            if not draft:
                return Response({'error': 'Черновик не найден'},
                                status=status.HTTP_404_NOT_FOUND)

            # Проверяем, есть ли связь с двигателем
            engine_acceptance = EngineAcceptance.objects.filter(
                engine_id=pk, acceptance=draft).first()

            if not engine_acceptance:
                return Response({'error': 'Двигатель не найден в черновике'},
                                status=status.HTTP_404_NOT_FOUND)

            new_status = request.data.get('accepted')
            if new_status not in dict(EngineAcceptance.ACCEPTED_CHOICES):
                return Response(
                    {'error': 'Недопустимое значение для status'},
                    status=status.HTTP_400_BAD_REQUEST)

            # Обновляем поле и сохраняем
            engine_acceptance.accepted = new_status
            engine_acceptance.save()

            serializer = EngineAcceptanceSerializer(instance=engine_acceptance)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except EngineAcceptance.DoesNotExist:
            return Response(
                {'error': 'Связь между двигателем и приёмкой не найдена'},
                status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Ошибка: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcceptanceListAPIView(APIView):
    @method_permission_classes((IsAuthenticated,))
    def get(self, request):
        acceptances = Acceptance.objects.all()

        if not request.user.is_staff:
            acceptances = acceptances.filter(
                creator=request.user
            ).exclude(
                status__in=['deleted', 'draft']
            )

        status_filter = request.query_params.get('status')
        date_start = request.query_params.get('date_start')
        date_end = request.query_params.get('date_end')

        if status_filter:
            acceptances = acceptances.filter(status=status_filter)
        if date_start:
            acceptances = acceptances.filter(formation_date__gte=date_start)
        if date_end:
            acceptances = acceptances.filter(
                formation_date__lte=date_end + ' 23:59:00')

        serializer = AcceptanceSerializer(acceptances, many=True)
        return Response(serializer.data)


class AcceptanceDetailAPIView(APIView):
    @method_permission_classes((IsAuthenticated,))
    def get(self, request, pk):
        try:
            acceptance = Acceptance.objects.get(pk=pk)

            if not (
                    acceptance.creator == request.user or request.user.is_staff):
                return Response({'error': 'Доступ запрещён'},
                                status=status.HTTP_403_FORBIDDEN)

            serializer = AcceptanceDetailSerializer(acceptance)
            response_data = serializer.data
            return Response(response_data)
        except ObjectDoesNotExist:
            return Response({'error': 'Приёмка не найдена'},
                            status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=AcceptanceSerializer)
    def put(self, request, pk):
        try:
            acceptance = Acceptance.objects.get(pk=pk)

            if not (
                    acceptance.creator == request.user or request.user.is_staff):
                return Response({'error': 'Доступ запрещён'},
                                status=status.HTTP_403_FORBIDDEN)

            if acceptance.status == 'deleted':
                return Response({'error': 'Приёмка удалена'},
                                status=status.HTTP_404_NOT_FOUND)

            serializer = AcceptanceSerializer(acceptance, data=request.data,
                                              partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Приёмка не найдена'},
                            status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            acceptance = Acceptance.objects.get(pk=pk)

            if not (
                    acceptance.creator == request.user or request.user.is_staff):
                return Response({'error': 'Доступ запрещён'},
                                status=status.HTTP_403_FORBIDDEN)

            if acceptance.status == 'deleted':
                return Response({'error': 'Приёмка уже удалена'},
                                status=status.HTTP_404_NOT_FOUND)

            acceptance.status = 'deleted'
            acceptance.save()
            return Response({'message': 'Приёмка успешно удалена'})

        except ObjectDoesNotExist:
            return Response({'error': 'Приёмка не найдена'},
                            status=status.HTTP_404_NOT_FOUND)


class AcceptanceFormAPIView(APIView):
    @method_permission_classes((IsAuthenticated,))
    def post(self, request, pk):
        try:
            acceptance = Acceptance.objects.get(pk=pk, status='draft')

            if not acceptance.creator == request.user:
                return Response({'error': 'Доступ запрещён'},
                                status=status.HTTP_403_FORBIDDEN)

            if not acceptance.title or not acceptance.name:
                return Response({'error': 'Обязательные поля не заполнены'},
                                status=status.HTTP_400_BAD_REQUEST)

            acceptance.status = 'formed'
            acceptance.formation_date = now()
            acceptance.save()
            return Response({'message': 'Приёмка успешно сформирована'},
                            status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(
                {
                    'error': 'Приёмка не найдена или не находится в статусе черновика'},
                status=status.HTTP_404_NOT_FOUND)


class AcceptanceCompleteRejectAPIView(APIView):
    @swagger_auto_schema(request_body=AcceptanceStatusSerializer)
    @method_permission_classes((IsModer,))
    def post(self, request, pk):
        try:
            acceptance = Acceptance.objects.get(pk=pk, status='formed')
            new_status = request.data.get('status')
            if new_status not in ['complete', 'reject']:
                return Response({'error': 'Недопустимый статус'},
                                status=status.HTTP_400_BAD_REQUEST)

            acceptance.completion_date = now()
            acceptance.moderator = request.user

            if new_status == 'complete':
                acceptance.status = 'completed'
                acceptance.total_accepted = EngineAcceptance.objects.filter(
                    acceptance=acceptance, accepted='accepted'
                ).count()
                qr_code_base64 = generate_acceptance_qr(
                    acceptance,
                    EngineAcceptance.objects.filter(acceptance=acceptance)
                )
                acceptance.qr = qr_code_base64
            elif new_status == 'reject':
                acceptance.status = 'rejected'

            acceptance.save()
            return Response({'message': f'Приёмка {new_status}'},
                            status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(
                {
                    'error': 'Приёмка не найдена или не находится в статусе сформирована'},
                status=status.HTTP_404_NOT_FOUND)


class UserRegistrationAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({
                'message': 'Пользователь успешно зарегистрирован',
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileUpdateAPIView(APIView):
    @swagger_auto_schema(request_body=UserSerializer)
    def put(self, request):
        try:
            user = request.user
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                ssid = request.COOKIES.get("session_id")
                session_storage.set(ssid, serializer.data['username'])
                return Response({
                    'message': 'Данные пользователя успешно обновлены',
                    **serializer.data
                })
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'},
                            status=status.HTTP_404_NOT_FOUND)


class UserLoginAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request):
        username = request.data['username']
        password = request.data['password']
        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response({"error": "Неверные данные для входа."},
                            status=status.HTTP_400_BAD_REQUEST)

        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)

        response = Response({
            'id': user.id,
            'username': user.username,
            'is_staff': user.is_staff,
        })

        response.set_cookie(
            "session_id",
            random_key,
            samesite="Lax",
            secure=True,
            httponly=True,  # можно True, если фронту не нужно читать куку из JS
            path="/",
            max_age=60 * 60 * 24 * 7,  # например, неделя
        )

        response.set_cookie(
            "csrftoken", get_token(request),
            samesite="Lax",
            secure=True,
            path="/",
        )
        return response


class UserLogoutAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        session_storage.delete(session_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AttributeAPIView(APIView):
    @swagger_auto_schema(method='get')
    def get(self, request, pk):
        engine = get_object_or_404(Engine, id=pk)

        all_attributes = Attribute.objects.all()

        response_data = []
        for attribute in all_attributes:
            engineattr = EngineAttribute.objects.filter(engine=engine,
                                                        attribute=attribute).first()
            response_data.append({
                'name': attribute.name,
                'value': engineattr.value if engineattr else None,
            })

        return Response({"attributes": response_data},
                        status=status.HTTP_200_OK)

    @swagger_auto_schema(method='post')
    @method_permission_classes((IsModer,))
    def post(self, request, pk):
        engine = get_object_or_404(Engine, id=pk)
        attribute_name = request.data.get("name")
        attribute_value = request.data.get("value")

        if not attribute_name or attribute_value is None:
            return Response(
                {"error": "Не заполнены обязательные поля."},
                status=status.HTTP_400_BAD_REQUEST
            )
        attribute, _ = Attribute.objects.get_or_create(name=attribute_name)

        route_attribute, created = EngineAttribute.objects.get_or_create(
            engine=engine, attribute=attribute,
            defaults={"value": attribute_value}
        )

        if not created:
            route_attribute.value = attribute_value
            route_attribute.save(update_fields=["value"])

        return Response(
            {"detail": f"Атрибут '{attribute_name}' успешно создан."},
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(method='delete')
    @method_permission_classes((IsModer,))
    def delete(self, request, pk):
        attribute_name = request.data.get("name")

        if not attribute_name:
            return Response({"error": "Необходимо ввести название атрибута."},
                            status=status.HTTP_400_BAD_REQUEST)

        attribute = Attribute.objects.filter(name=attribute_name).first()
        if not attribute:
            return Response(
                {"error": f"Атрибут '{attribute_name}' не существует."},
                status=status.HTTP_404_NOT_FOUND)

        attribute.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(method='put')
    @method_permission_classes((IsModer,))
    def put(self, request, pk):
        engine = get_object_or_404(Engine, id=pk)
        attribute_name = request.data.get("name")
        attribute_value = request.data.get("value")

        if not attribute_name:
            return Response(
                {"error": "Введите название атрибута."},
                status=status.HTTP_400_BAD_REQUEST)

        attribute = Attribute.objects.filter(name=attribute_name).first()
        if not attribute:
            return Response(
                {"error": f"Attribute '{attribute_name}' not found."},
                status=status.HTTP_404_NOT_FOUND)

        route_attribute = EngineAttribute.objects.filter(engine=engine,
                                                         attribute=attribute).first()

        if not route_attribute:
            EngineAttribute.objects.create(engine=engine,
                                           attribute=attribute,
                                           value=attribute_value)
            return Response({"name": attribute_name,
                             "value": attribute_value,
                             "status": "created"},
                            status=status.HTTP_201_CREATED)

        if not attribute_value:
            route_attribute.delete()
            return Response({"status": "deleted"},
                            status=status.HTTP_204_NO_CONTENT)

        route_attribute.value = attribute_value
        route_attribute.save(update_fields=["value"])
        return Response({"name": attribute_name,
                         "value": attribute_value,
                         "status": "updated"},
                        status=status.HTTP_200_OK)
