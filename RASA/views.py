from django.shortcuts import render, redirect
from .models import Service

# Вьюха для главной страницы
from django.shortcuts import render


def homepage_view(request):
    query = request.GET.get('q', '')  # Получаем значение из поискового запроса (по умолчанию пустая строка)

    # Определяем список карточек для фильтрации
    services = [
        {'name': 'Определение состава партии', 'description': 'Описание услуги', 'image_url': 'RASA/icon1.png'},
        {'name': 'Подготовка документации', 'description': 'Описание услуги', 'image_url': 'RASA/icon2.png'},
        {'name': 'Проверка технических характеристик', 'description': 'Описание услуги', 'image_url': 'RASA/icon3.png'},
        {'name': 'Контроль качества', 'description': 'Описание услуги', 'image_url': 'RASA/icon4.png'},
        {'name': 'Оформление результатов', 'description': 'Описание услуги', 'image_url': 'RASA/icon5.png'},
        {'name': 'Передача информации заказчику', 'description': 'Описание услуги', 'image_url': 'RASA/icon6.png'}
    ]
    # Фильтруем карточки по запросу
    if query:
        filtered_services = [service for service in services if query.lower() in service['name'].lower()]
    else:
        filtered_services = services  # Если запрос пуст, показываем все карточки

    return render(request, 'RASA/homepage.html', {'services': filtered_services, 'query': query})


# Данные об услугах (их можно хранить в базе данных)
services_data = {
    'Определение состава партии': {
        'description': 'Проводится согласование объемов партии, закладываются характеристики и материалы',
        'description_en': 'The volume of the batch is being coordinated, characteristics and materials are being laid down',
        'service_data': 'ГОСТ Р 52745-2007',
        'service_data_en': 'State Standard 52745-2007',
        'service_name_en': 'Batch Composition Definition',
        'image_url': 'icon1.png'
    },
    'Подготовка документации': {
        'description': 'Подготовка всей необходимой документации и паспортов партии, разработка чертежей',
        'description_en': 'Preparation of all necessary documentation and batch passports, development of drawings',
        'service_data': 'ГОСТ Р 52745-2007',
        'service_data_en': 'State Standard 52745-2007',
        'service_name_en': 'Preparation of docs',
        'image_url': 'icon2.png'
    },
    'Проверка технических характеристик': {
        'description': 'Проведение тестов на установление технических характеристик',
        'description_en': 'Conducting tests to establish technical characteristics',
        'service_data': 'ГОСТ Р 52745-2007',
        'service_data_en': 'State Standard 52745-2007',
        'service_name_en': 'Check of the technical characteristics',
        'image_url': 'icon3.png'
    },
    'Контроль качества': {
        'description': 'Проведение необходимых испытаний на долговечность, нагрузку, брак, и настройку авиадвигателей',
        'description_en': 'Carrying out the necessary tests for durability, load, marriage, and tuning of aircraft engines',
        'service_data': 'ГОСТ Р 52745-2007',
        'service_data_en': 'State Standard 52745-2007',
        'service_name_en': 'Quality control',
        'image_url': 'icon4.png'
    },
    'Оформление результатов': {
        'description': 'Составление техпаспорта партии и моделей',
        'description_en': 'Drawing up the technical passport of the batch and models',
        'service_data': 'ГОСТ Р 52745-2007',
        'service_data_en': 'State Standard 52745-2007',
        'service_name_en': 'Design of the butch results',
        'image_url': 'icon5.png'
    },
    'Передача информации заказчику': {
        'description': 'Передача полной документации и готовой партии заказчику',
        'description_en': 'Transfer of the complete documentation and the finished batch to the customer',
        'service_data': 'ГОСТ Р 52745-2007',
        'service_data_en': 'State Standard 52745-2007',
        'service_name_en': 'Deliver documents to the customer',
        'image_url': 'icon6.png'
    },

}


def info_view(request):
    service_name = request.GET.get('service', '')
    service = services_data.get(service_name)

    if service:
        return render(request, 'RASA/info.html', {
            'service': service,
            'service_name': service_name,
            'service_name_en': service['service_name_en'],  # Перевод названия
        })
    else:
        return render(request, 'RASA/404.html')


# Вьюха для страницы корзины
def cart_page(request):
    cart_services = request.session.get('cart', [])
    query = request.GET.get('query', '').strip().lower()
    if query:
        filtered_services = [service for service in cart_services if query in service.lower()]
    else:
        filtered_services = cart_services
    return render(request, 'RASA/cart.html', {'cart_services': filtered_services})


# Вьюха для добавления товара в корзину
def add_to_cart(request):
    if request.method == 'POST':
        item = request.POST.get('item_name', '')  # Получаем название услуги из формы

        # Проверяем, есть ли корзина в сессии, если нет — создаем
        cart = request.session.get('cart', [])

        # Проверяем, есть ли уже этот товар в корзине
        if item not in cart:
            # Если товара нет в корзине, добавляем его
            cart.append(item)
            request.session['cart'] = cart  # Сохраняем обновленную корзину в сессии
            print(f"Текущая корзина: {request.session['cart']}")
        else:
            print(f"Товар {item} уже в корзине.")

    # Перенаправляем на страницу корзины или обратно
    return redirect('homepage')


def remove_from_cart(request):
    if request.method == 'POST':
        item = request.POST.get('item_name', '')  # Получаем название услуги из формы

        # Проверяем, есть ли корзина в сессии
        cart = request.session.get('cart', [])

        # Удаляем товар, если он есть в корзине
        if item in cart:
            cart.remove(item)
            request.session['cart'] = cart

    # Перенаправляем обратно на страницу корзины
    return redirect('cart_page')


def service_search(request):
    # Получаем значение из поискового поля
    query = request.GET.get('query', '').strip().lower()

    # Если введен запрос, ищем карточки, которые содержат введенный текст
    if query:
        services = Service.objects.filter(title__icontains=query)  # Фильтрация по названию, игнорируя регистр
    else:
        # Если запрос пустой, отображаем все карточки
        services = Service.objects.all()

    # Отправляем данные в шаблон
    return render(request, 'RASA/homepage.html', {'services': services, 'query': query})
