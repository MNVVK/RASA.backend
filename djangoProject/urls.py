from RASA import views
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage_view, name='homepage'),  # Главная страница
    path('engines/<int:id>/', views.engines_view, name='engines_page'),  # Страница двигателя
    path('acceptance/<int:id>', views.acceptance_page, name='acceptance_page'),  # Страница корзины
    path('engines/', views.engine_search, name='engine_search'),  # Путь для поиска услуг
    #path('add-to-acceptance/<int:id>/', views.add_to_acceptance, name='add_to_acceptance'),  # Убрать для 1 лабы Добавление в корзину
    #path('remove-from-acceptance/', views.remove_from_acceptance, name='remove_from_acceptance')  # Убрать дял 1 лабы Новый путь для удаления
]
