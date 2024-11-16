from django.shortcuts import redirect
# Вьюха для главной страницы
from django.shortcuts import render

from .models import Engine


def homepage_view(request):
    query = request.GET.get('engine_name',
                            '')  # Получаем значение из поискового запроса (по умолчанию пустая строка)

    # Определяем список карточек для фильтрации
    engines = [
        {'id': 1, 'name': 'RASA. FJ-44', 'description': 'Описание услуги',
         'image_url': 'http://localhost:9000/rasa/fj-44.png'},
        {'id': 2, 'name': 'RASA. CFM-56', 'description': 'Описание услуги',
         'image_url': 'http://localhost:9000/rasa/cfm-56.png'},
        {'id': 3, 'name': 'RASA. BNG-737', 'description': 'Описание услуги',
         'image_url': 'http://localhost:9000/rasa/bng-737.png'},
        {'id': 4, 'name': 'RASA. LEAP', 'description': 'Описание услуги',
         'image_url': 'http://localhost:9000/rasa/leap.png'},
        {'id': 5, 'name': 'RASA. AP-1', 'description': 'Описание услуги',
         'image_url': 'http://localhost:9000/rasa/ap-1.png'},
        {'id': 6, 'name': 'RASA. CFM-57', 'description': 'Описание услуги',
         'image_url': 'http://localhost:9000/rasa/cfm-57.png'}
    ]
    # Фильтруем карточки по запросу
    if query:
        filtered_engines = [engine for engine in engines if
                            query.lower() in engine['name'].lower()]
    else:
        filtered_engines = engines  # Если запрос пуст, показываем все карточки

    return render(request, 'RASA/homepage.html',
                  {'engines': filtered_engines, 'query': query})


# Данные об услугах
engines_data = [
    {
        'id': 1,
        'title': 'RASA. FJ-44',
        'description': 'Надежный, крепкий двигатель, сконструированный для легкости обслуживания. Уникальный дизайн двигателя позволяет заменять детали пока двигатель установлен на судне.',
        'description_en': 'Reliable, robust engine, designed for ease of maintenance. The unique design of the engine allows you to replace parts while the engine is installed on the ship.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'image_url': 'http://localhost:9000/rasa/fj-44.png'
    },
    {
        'id': 2,
        'title': 'RASA. CFM-56',
        'description': 'Всемирно известный и универсальный аивадвигатель, предназначен для однопроходных коммерческих лайнеров, а также для различных военных самолетов.',
        'description_en': 'The world-famous and versatile aircraft engine is designed for single-aisle commercial airliners, as well as for various military aircraft.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'image_url': 'http://localhost:9000/rasa/cfm-56.png'
    },
    {
        'id': 3,
        'title': 'RASA. BNG-737',
        'description': 'Исключительно надежный, самый продаваемый двигатель в мире за всю историю авиации. На сегодняшний день поставлено более 33 000 двигателей, которыми оснащаются в основном однопроходные коммерческие самолеты Boeing.',
        'description_en': 'Exceptionally reliable, the best-selling engine in the world in the history of aviation. To date, more than 33,000 engines have been delivered, which are mainly equipped with single-aisle Boeing commercial aircraft.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'image_url': 'http://localhost:9000/rasa/bng-737.png'
    },
    {
        'id': 4,
        'title': 'RASA. LEAP',
        'description': 'Экологически чистый двигатель, разработанный для решения задачи декарбонизации воздушного транспорта, предлагает операторам самолетов улучшенные показатели расхода топлива и выбросов CO2, выбросов NOx и шума.',
        'description_en': 'The environmentally friendly engine, designed to solve the problem of decarbonization of air transport, offers aircraft operators improved fuel consumption and CO2 emissions, NOx emissions and noise.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'image_url': 'http://localhost:9000/rasa/leap.png'
    },
    {
        'id': 5,
        'title': 'RASA. AP-1',
        'description': 'Легкий и мощный двигатель, разработанный специально для частных летательных судов. Обеспечивает высокую надежность и простоту в обслуживании, идеально подходя для долгосрочной эксплуатации и комфортных тихих полетов.',
        'description_en': 'A lightweight and powerful engine designed specifically for private aircraft. It provides high reliability and ease of maintenance, ideal for long-term operation and comfortable quiet flights.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'image_url': 'http://localhost:9000/rasa/ap-1.png'
    },
    {
        'id': 6,
        'title': 'RASA. CFM-57',
        'description': 'Высокотехнологичный и адаптивный авиадвигатель, младшая модель CFM-56, разработан для обеспечения максимальной производительности и упрощения технического обслуживания, конструкция позволяет легко проводить замену компонентов без снятия двигателя. Идеально подходит для широкого спектра коммерческих и военных летательных аппаратов, обеспечивая надёжность и эффективность при различных условиях эксплуатации.',
        'description_en': 'The high-tech and adaptive aircraft engine, the junior CFM-56 model, is designed to maximize performance and simplify maintenance, the design makes it easy to replace components without removing the engine. It is ideal for a wide range of commercial and military aircraft, providing reliability and efficiency under various operating conditions.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'image_url': 'http://localhost:9000/rasa/cfm-57.png'
    },

]

# Данные об заявках
acceptance_data = [
    {
        'id': 1,
        'title': 'Заключительный тест приёмки',
        'status': 'draft'
    },
]

# Модель многие-ко-многим
acceptance_engines = [
    {
        'acceptance': 1,
        'engine': 1,
        'status': 'Принят'
    },
    {
        'acceptance': 1,
        'engine': 3,
        'status': 'Принят',
    },
    {
        'acceptance': 1,
        'engine': 5,
        'status': 'Не принят'
    },
]


def engines_view(request, id):
    engine = engines_data[id - 1]

    if engine:
        return render(request, 'RASA/engines.html', {
            'engine': engine,
        })
    else:
        return render(request, 'RASA/404.html')


# Вьюха для страницы корзины
def acceptance_page(request, id):
    acceptance = acceptance_data[id - 1]
    filtred_engines = [
        {
            'engine': engines_data[item['engine'] - 1],
            'status': item['status']
        } for item in acceptance_engines if item['acceptance'] == id
    ]
    return render(request, 'RASA/acceptance.html',
                  {'acceptance': acceptance,
                   'acceptance_engines': filtred_engines})


# Вьюха для добавления товара в корзину (НЕ НУЖНО В 1 ЛАБЕ)
def add_to_acceptance(request, id):
    if request.method == 'POST':
        # Проверяем, есть ли корзина в сессии, если нет — создаем
        acceptance = request.session.get('acceptance', [])

        # Проверяем, есть ли уже этот товар в корзине
        if id not in acceptance:
            # Если товара нет в корзине, добавляем его
            acceptance.append(id)
            request.session[
                'acceptance'] = acceptance  # Сохраняем обновленную корзину в сессии
            print(f"Текущая корзина: {request.session['acceptance']}")
        else:
            print(f"Товар с ID {id} уже в корзине.")

    # Перенаправляем на страницу корзины или обратно
    return redirect('homepage')


# (НЕ НУЖНО В 1 ЛАБЕ)
def remove_from_acceptance(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')  # Получаем ID услуги из формы

        # Проверяем, есть ли корзина в сессии
        acceptance = request.session.get('acceptance', [])

        # Удаляем товар по ID, если он есть в корзине
        if item_id and int(item_id) in acceptance:
            acceptance.remove(int(item_id))
            request.session[
                'acceptance'] = acceptance  # Сохраняем обновленную корзину в сессии

    # Перенаправляем обратно на страницу корзины
    return redirect('acceptance_page')


def engine_search(request):
    # Получаем значение из поискового поля
    query = request.GET.get('query', '').strip().lower()

    # Если введен запрос, ищем карточки, которые содержат введенный текст
    if query:
        engines = Engine.objects.filter(
            title__icontains=query)  # Фильтрация по названию, игнорируя регистр
    else:
        # Если запрос пустой, отображаем все карточки
        engines = Engine.objects.all()

    # Отправляем данные в шаблон
    return render(request, 'RASA/homepage.html',
                  {'engines': engines, 'query': query})

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Service, Application, ApplicationService
from django.db import connection

def list_services(request):
    services = Service.objects.filter(status='active')
    return render(request, 'services/list.html', {'services': services})

def view_application(request, application_id):
    application = get_object_or_404(Application, id=application_id, status__in=['draft', 'formed'])
    return render(request, 'applications/view.html', {'application': application})

def add_service_to_application(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    application, created = Application.objects.get_or_create(creator=request.user, status='draft')
    ApplicationService.objects.create(application=application, service=service)
    return redirect('view_application', application_id=application.id)

def delete_application(request, application_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE app_application SET status='deleted' WHERE id=%s", [application_id])
    return HttpResponse("Application logically deleted.")

