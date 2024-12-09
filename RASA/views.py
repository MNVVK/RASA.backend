from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from minio import Minio
from minio.error import S3Error
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Engine, Acceptance, EngineAcceptance
from .serializers import (
    EngineSerializer, AcceptanceSerializer,
    AcceptanceDetailSerializer, UserSerializer
)

CONST_USER = User.objects.get(pk=1)


class EngineListAPIView(APIView):
    def get(self, request):
        # Исключаем удалённые двигатели
        engines = Engine.objects.exclude(status='deleted')

        if 'engine_title' in request.query_params:
            engine_title = request.query_params['engine_title']
            engines = engines.filter(title__icontains=engine_title)

        serializer = EngineSerializer(engines, many=True)
        user = CONST_USER
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

    def put(self, request, pk):
        try:
            engine = Engine.objects.get(pk=pk)
            if engine.status == 'deleted':
                return Response({'error': 'Этот двигатель удалён'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = EngineSerializer(engine, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Engine.DoesNotExist:
            return Response({'error': 'Двигатель не найден или удалён'},
                            status=status.HTTP_404_NOT_FOUND)

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
    def post(self, request, pk):
        try:
            engine = Engine.objects.get(pk=pk)
            if engine.status == 'deleted':
                return Response({'error': 'Этот двигатель удалён'},
                                status=status.HTTP_400_BAD_REQUEST)
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
                return Response({'error': 'Этот двигатель удалён и не может быть добавлен в черновик'},
                                status=status.HTTP_400_BAD_REQUEST)

            draft, created = Acceptance.objects.get_or_create(
                creator=CONST_USER, status='draft',
            )
            if EngineAcceptance.objects.filter(engine=engine, acceptance=draft).exists():
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
            user = CONST_USER
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
                {'message': 'Двигатель успешно удалён из черновика'},)
        except Exception as e:
            return Response({'error': f'Ошибка: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            user = CONST_USER
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

            new_status = request.data.get('status')
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
    def get(self, request):
        acceptances = Acceptance.objects.exclude(
            status__in=['deleted', 'draft'])
        status_filter = request.query_params.get('status')
        date_start = request.query_params.get('date_start')
        date_end = request.query_params.get('date_end')

        if status_filter:
            acceptances = acceptances.filter(status=status_filter)
        if date_start and date_end:
            acceptances = acceptances.filter(
                formation_date__range=[date_start, date_end])

        serializer = AcceptanceSerializer(acceptances, many=True)
        return Response(serializer.data)


class AcceptanceDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            acceptance = Acceptance.objects.get(pk=pk)
            serializer = AcceptanceDetailSerializer(acceptance)
            response_data = serializer.data
            return Response(response_data)
        except ObjectDoesNotExist:
            return Response({'error': 'Приёмка не найдена'},
                            status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            acceptance = Acceptance.objects.get(pk=pk)
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
    def post(self, request, pk):
        try:
            acceptance = Acceptance.objects.get(pk=pk, status='formed')
            new_status = request.data.get('status')
            if new_status not in ['complete', 'reject']:
                return Response({'error': 'Недопустимый статус'},
                                status=new_status.HTTP_400_BAD_REQUEST)

            acceptance.completion_date = now()
            acceptance.moderator = CONST_USER

            if new_status == 'complete':
                acceptance.status = 'completed'
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
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Пользователь успешно зарегистрирован',
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileUpdateAPIView(APIView):
    def put(self, request):
        try:
            user = CONST_USER
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
    def post(self, request):
        return Response({'message': 'Аутентификация успешно выполнена'},
                        status=status.HTTP_200_OK)


class UserLogoutAPIView(APIView):
    def post(self, request):
        return Response({'message': 'Вы успешно вышли из системы'},
                        status=status.HTTP_200_OK)
