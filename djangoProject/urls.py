from RASA import views
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage_view, name='homepage'),  # Главная страница
    path('info/', views.info_view, name='info_page'),  # Вторая страница
    path('cart/', views.cart_page, name='cart_page'),  # Страница корзины
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),  # Добавление в корзину
    path('services/', views.service_search, name='service_search'),  # Ваш путь для поиска услуг
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart')  # Новый путь для удаления
]
