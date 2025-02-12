import uuid
from urllib.parse import urlparse

import redis
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from minio import Minio
from minio.error import S3Error
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Engine, Acceptance, EngineAcceptance
from .permissions import IsModer
from .serializers import (
    EngineSerializer, AcceptanceSerializer,
    AcceptanceDetailSerializer, UserSerializer, EngineAcceptanceSerializer,
    AcceptanceStatusSerializer,
)

User = get_user_model()

session_storage = redis.StrictRedis(host=settings.REDIS_HOST,
                                    port=settings.REDIS_PORT)


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
        engines = Engine.objects.exclude(status='deleted')

        if 'engine_title' in request.query_params:
            engine_title = request.query_params['engine_title']
            engines = engines.filter(title__icontains=engine_title)

        serializer = EngineSerializer(engines, many=True)
        user = request.user
        draft = Acceptance.objects.filter(creator=user, status='draft').first()
        draft_id = draft.id if draft else None
        draft_engines_count = EngineAcceptance.objects.filter(
            acceptance=draft).count() if draft else 0

        response_data = {
            'draft_id': draft_id,
            'draft_engines_count': draft_engines_count,
            'data': serializer.data
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

            # Удаляем файл из MinIO, если он существует
            if engine.image_url:
                try:
                    parsed_url = urlparse(engine.image_url)
                    bucket_name = settings.MINIO_BUCKET_NAME
                    object_name = parsed_url.path.lstrip('/')

                    minio_client = Minio(
                        settings.MINIO_ENDPOINT,
                        access_key=settings.MINIO_ACCESS_KEY,
                        secret_key=settings.MINIO_SECRET_KEY,
                        secure=settings.MINIO_SECURE,
                    )
                    minio_client.remove_object(bucket_name, object_name)

                except S3Error as e:
                    return Response({'error': f'Ошибка MinIO: {str(e)}'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Exception as e:
                    return Response({
                        'error': f'Общая ошибка при удалении из MinIO: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            engine.image_url = None
            engine.status = 'deleted'
            engine.save()

            return Response({'message': 'Двигатель успешно удалён'})
        except Engine.DoesNotExist:
            return Response({'error': 'Двигатель не найден или удалён'},
                            status=status.HTTP_404_NOT_FOUND)


class EngineAddImageAPIView(APIView):
    @method_permission_classes((IsModer,))
    def post(self, request, pk):
        try:
            engine = Engine.objects.get(pk=pk)

            file = request.FILES.get('image')
            if not file:
                return Response({'error': 'Файл изображения не передан'},
                                status=status.HTTP_400_BAD_REQUEST)

            minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )

            bucket_name = settings.MINIO_BUCKET_NAME

            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)

            file_name = f"engines/{engine.id}/{file.name}"
            minio_client.put_object(
                bucket_name=bucket_name,
                object_name=file_name,
                data=file,
                length=file.size,
                content_type=file.content_type
            )

            image_url = f"{settings.MINIO_BASE_URL}/{bucket_name}/{file_name}"
            engine.image_url = image_url
            engine.save()

            return Response(
                {'message': 'Изображение успешно добавлено', 'url': image_url},
                status=status.HTTP_200_OK)

        except Engine.DoesNotExist:
            return Response({'error': 'Двигатель не найден или удалён'},
                            status=status.HTTP_404_NOT_FOUND)
        except S3Error as e:
            return Response({'error': f'Ошибка MinIO: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddEngineToDraftAPIView(APIView):
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

            EngineAcceptance.objects.create(engine=engine, acceptance=draft)
            return Response({'message': 'Двигатель добавлен в черновик'},
                            status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Двигатель не найден'},
                            status=status.HTTP_404_NOT_FOUND)


class DraftEngineManagementAPIView(APIView):
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

            return Response({'message': 'Поле успешно обновлено'},
                            status=status.HTTP_200_OK)
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
        if date_start and date_end:
            if date_start == date_end:
                acceptances = acceptances.filter(formation_date=date_start)
            else:
                acceptances = acceptances.filter(
                    formation_date__range=[date_start, date_end + ' 23:59:00'])
        elif date_start:
            acceptances = acceptances.filter(formed_at__gte=date_start)
        elif date_end:
            acceptances = acceptances.filter(formed_at__lte=date_end)

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
                return Response({
                    'message': 'Данные пользователя успешно обновлены',
                    'user': serializer.data
                })
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'},
                            status=status.HTTP_404_NOT_FOUND)


class UserLoginAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    @csrf_exempt
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
        response.set_cookie("session_id", random_key)

        return response


class UserLogoutAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @csrf_exempt
    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        session_storage.delete(session_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
