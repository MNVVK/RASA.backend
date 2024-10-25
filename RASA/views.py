from django.shortcuts import render, redirect
from .models import Engine

# Вьюха для главной страницы
from django.shortcuts import render


def homepage_view(request):
    query = request.GET.get('q', '')  # Получаем значение из поискового запроса (по умолчанию пустая строка)

    # Определяем список карточек для фильтрации
    engines = [
        {'id': 1, 'name': 'Определение состава партии', 'description': 'Описание услуги',
         'image_url': 'RASA/fj44.png'},
        {'id': 2, 'name': 'Подготовка документации', 'description': 'Описание услуги', 'image_url': 'RASA/pngg.png'},
        {'id': 3, 'name': 'Проверка технических характеристик', 'description': 'Описание услуги',
         'image_url': 'RASA/boeng 737.png'},
        {'id': 4, 'name': 'Контроль качества', 'description': 'Описание услуги', 'image_url': 'RASA/cfm leap.png'},
        {'id': 5, 'name': 'Оформление результатов', 'description': 'Описание услуги', 'image_url': 'RASA/121212.png'},
        {'id': 6, 'name': 'Передача информации заказчику', 'description': 'Описание услуги',
         'image_url': 'RASA/pngegg.png'}
    ]
    # Фильтруем карточки по запросу
    if query:
        filtered_engines = [engine for engine in engines if query.lower() in engine['name'].lower()]
    else:
        filtered_engines = engines  # Если запрос пуст, показываем все карточки

    return render(request, 'RASA/homepage.html', {'engines': filtered_engines, 'query': query})


# Данные об услугах (их можно хранить в базе данных)
engines_data = [
    {
        'id': 1,
        'title': 'Определение состава партии',
        'description': 'Проводится согласование объемов партии, закладываются характеристики и материалы',
        'description_en': 'The volume of the batch is being coordinated, characteristics and materials are being laid down',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'engine_name_en': 'Batch Composition Definition',
        'image_url': 'fj44.png'
    },
    {
        'id': 2,
        'title': 'Подготовка документации',
        'description': 'Подготовка всей необходимой документации и паспортов партии, разработка чертежей',
        'description_en': 'Preparation of all necessary documentation and batch passports, development of drawings',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'engine_name_en': 'Preparation of docs',
        'image_url': 'pngg.png'
    },
    {
        'id': 3,
        'title': 'Проверка технических характеристик',
        'description': 'Проведение тестов на установление технических характеристик',
        'description_en': 'Conducting tests to establish technical characteristics',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'engine_name_en': 'Check of the technical characteristics',
        'image_url': 'boeng 737.png'
    },
    {
        'id': 4,
        'title': 'Контроль качества',
        'description': 'Проведение необходимых испытаний на долговечность, нагрузку, брак, и настройку авиадвигателей',
        'description_en': 'Carrying out the necessary tests for durability, load, marriage, and tuning of aircraft engines',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'engine_name_en': 'Quality control',
        'image_url': 'cfm leap.png'
    },
    {
        'id': 5,
        'title': 'Оформление результатов',
        'description': 'Составление техпаспорта партии и моделей',
        'description_en': 'Drawing up the technical passport of the batch and models',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'engine_name_en': 'Design of the butch results',
        'image_url': '121212.png'
    },
    {
        'id': 6,
        'title': 'Передача информации заказчику',
        'description': 'Передача полной документации и готовой партии заказчику',
        'description_en': 'Transfer of the complete documentation and the finished batch to the customer',
        'engine_data': 'ГОСТ Р 52745-2007',
        'engine_data_en': 'State Standard 52745-2007',
        'engine_name_en': 'Deliver documents to the customer',
        'image_url': 'pngegg.png'
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
def acceptance_page(request):
    acceptance_engines = request.session.get('acceptance', [])

    # Порядок услуг как на homepage
    all_engines = {engine['id']: engine for engine in engines_data}  # Преобразуем список в словарь для быстрого поиска по id

    # Фильтруем те элементы, которые есть в корзине по их ID
    sorted_acceptance_engines = [all_engines[engine_id] for engine_id in acceptance_engines if engine_id in all_engines]

    query = request.GET.get('query', '').strip().lower()
    if query:
        filtered_engines = [engine for engine in sorted_acceptance_engines if query in engine['title'].lower()]
    else:
        filtered_engines = sorted_acceptance_engines

    return render(request, 'RASA/acceptance.html', {'acceptance_engines': filtered_engines})


# Вьюха для добавления товара в корзину
def add_to_acceptance(request, id):
    if request.method == 'POST':
        # Проверяем, есть ли корзина в сессии, если нет — создаем
        acceptance = request.session.get('acceptance', [])

        # Проверяем, есть ли уже этот товар в корзине
        if id not in acceptance:
            # Если товара нет в корзине, добавляем его
            acceptance.append(id)
            request.session['acceptance'] = acceptance  # Сохраняем обновленную корзину в сессии
            print(f"Текущая корзина: {request.session['acceptance']}")
        else:
            print(f"Товар с ID {id} уже в корзине.")

    # Перенаправляем на страницу корзины или обратно
    return redirect('homepage')



def remove_from_acceptance(request):
    if request.method == 'POST':
        item = request.POST.get('item_name', '')  # Получаем название услуги из формы

        # Проверяем, есть ли корзина в сессии
        acceptance = request.session.get('acceptance', [])

        # Удаляем товар, если он есть в корзине
        if item in acceptance:
            acceptance.remove(item)
            request.session['acceptance'] = acceptance

    # Перенаправляем обратно на страницу корзины
    return redirect('acceptance_page')


def engine_search(request):
    # Получаем значение из поискового поля
    query = request.GET.get('query', '').strip().lower()

    # Если введен запрос, ищем карточки, которые содержат введенный текст
    if query:
        engines = Engine.objects.filter(title__icontains=query)  # Фильтрация по названию, игнорируя регистр
    else:
        # Если запрос пустой, отображаем все карточки
        engines = Engine.objects.all()

    # Отправляем данные в шаблон
    return render(request, 'RASA/homepage.html', {'engines': engines, 'query': query})
