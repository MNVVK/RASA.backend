from django.contrib import admin
from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from RASA.views import (
    EngineListAPIView,
    EngineDetailAPIView,
    EngineAddImageAPIView,
    AddEngineToDraftAPIView,
    AcceptanceListAPIView,
    AcceptanceDetailAPIView,
    AcceptanceFormAPIView,
    AcceptanceCompleteRejectAPIView, UserRegistrationAPIView,
    UserProfileUpdateAPIView, UserLoginAPIView, UserLogoutAPIView,
    DraftEngineManagementAPIView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="RASA API",
        default_version='v1',
        description="RASA Web Service",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Engine
    path('api/engines/', EngineListAPIView.as_view(), name='engine-list'),
    # GET, POST
    path('api/engines/<int:pk>/', EngineDetailAPIView.as_view(),
         name='engine-detail'),  # GET, PUT, DELETE
    path('api/engines/<int:pk>/add-image/', EngineAddImageAPIView.as_view(),
         name='engine-add-image'),  # POST
    path('api/engines/<int:pk>/add-to-draft/',
         AddEngineToDraftAPIView.as_view(),
         name='engine-add-to-draft'),  # POST
    path('api/engines/<int:pk>/manage-draft/',
         DraftEngineManagementAPIView.as_view(),
         name='engine-manage-draft'),  # PUT, DELETE

    # Acceptance
    path('api/acceptances/', AcceptanceListAPIView.as_view(),
         name='acceptance-list'),  # GET
    path('api/acceptances/<int:pk>/', AcceptanceDetailAPIView.as_view(),
         name='acceptance-detail'),  # GET, PUT
    path('api/acceptances/<int:pk>/form/', AcceptanceFormAPIView.as_view(),
         name='acceptance-form'),  # PUT
    path('api/acceptances/<int:pk>/moderate/',
         AcceptanceCompleteRejectAPIView.as_view(),
         name='acceptance-complete-reject'),  # PUT

    # User
    path('api/register/', UserRegistrationAPIView.as_view(),
         name='user-register'),

    path('api/profile/', UserProfileUpdateAPIView.as_view(),
         name='user-profile-update'),

    path('api/login/', UserLoginAPIView.as_view(), name='user-login'),

    path('api/logout/', UserLogoutAPIView.as_view(), name='user-logout'),

    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),

]
