from RASA import views
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage_view, name='homepage'),  # Главная страница
    path('engines/<int:id>/', views.engines_view, name='engines_page'),  # Страница двигателя
    path('acceptance/<int:id>', views.acceptance_page, name='acceptance_page'),  # Страница корзины
    path('add-to-acceptance/<int:id>/', views.add_to_acceptance, name='add_to_acceptance'),
    path('delete-acceptance/<int:id>/', views.delete_acceptance, name='delete_acceptance')
]
