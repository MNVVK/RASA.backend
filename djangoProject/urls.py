from django.contrib import admin
from django.urls import path

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

urlpatterns = [
    path('admin/', admin.site.urls),

    # Engine
    path('api/engines/', EngineListAPIView.as_view(), name='engine-list'),
    # GET, POST
    path('api/engines/<int:pk>/', EngineDetailAPIView.as_view(),
         name='engine-detail'),  # GET, PUT, DELETE
    path('api/engines/<int:pk>/add-image/', EngineAddImageAPIView.as_view(),
         name='engine-add-image'),  # POST
    path('api/engines/<int:pk>/add-to-draft/', AddEngineToDraftAPIView.as_view(),
         name='engine-add-to-draft'),  # POST
    path('api/engines/<int:pk>/manage-draft/', DraftEngineManagementAPIView.as_view(),
         name='engine-manage-draft'),  # PUT, DELETE

    # Acceptance
    path('api/acceptances/', AcceptanceListAPIView.as_view(),
         name='acceptance-list'),  # GET
    path('api/acceptances/<int:pk>/', AcceptanceDetailAPIView.as_view(),
         name='acceptance-detail'),  # GET, PUT
    path('api/acceptances/<int:pk>/form/', AcceptanceFormAPIView.as_view(),
         name='acceptance-form'),  # PUT
    path('api/acceptances/<int:pk>/status/',
         AcceptanceCompleteRejectAPIView.as_view(),
         name='acceptance-complete-reject'),  # PUT

    # User
    path('api/register/', UserRegistrationAPIView.as_view(), name='user-register'),

    path('api/profile/', UserProfileUpdateAPIView.as_view(),
         name='user-profile-update'),

    path('api/login/', UserLoginAPIView.as_view(), name='user-login'),

    path('api/logout/', UserLogoutAPIView.as_view(), name='user-logout'),
]
