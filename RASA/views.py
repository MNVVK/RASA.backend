from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Subquery, OuterRef
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render

from .models import Engine, Acceptance, EngineAcceptance

@login_required
def homepage_view(request):
    query = request.GET.get('engine_name', '').strip().lower()  # Получаем поисковый запрос

    # Фильтруем двигатели на основе запроса
    if query:
        engines = Engine.objects.filter(title__icontains=query)
    else:
        engines = Engine.objects.all()

    # Проверяем, есть ли у текущего пользователя драфтовая приемка
    draft_acceptance = Acceptance.objects.filter(creator=request.user, status='draft').first()

    # Определяем draft_id и draft_count
    draft_id = draft_acceptance.id if draft_acceptance else None
    draft_count = (
        EngineAcceptance.objects.filter(acceptance=draft_acceptance).count()
        if draft_acceptance else 0
    )

    # Возвращаем данные в шаблон
    return render(request, 'RASA/homepage.html', {
        'engines': engines,
        'query': query,
        'draft_id': draft_id,
        'draft_count': draft_count,
    })


def engines_view(request, id):
    engine = get_object_or_404(Engine, id=id)
    return render(request, 'RASA/engines.html', {'engine': engine})


def acceptance_page(request, id):
    acceptance = get_object_or_404(Acceptance, id=id)

    if acceptance.status == 'deleted':
        return redirect('homepage')

    acceptance_engines = Engine.objects.filter(
        engineacceptance__acceptance=acceptance).annotate(
        accepted=Subquery(
            EngineAcceptance.objects.filter(
                engine=OuterRef('pk'), acceptance=acceptance
            ).values('accepted')[:1]
        )
    )

    return render(request, 'RASA/acceptance.html', {
        'acceptance': acceptance,
        'acceptance_engines': acceptance_engines
    })


@login_required
def add_to_acceptance(request, id):
    if request.method == 'POST':
        user = request.user

        # Проверяем, существует ли у пользователя приемка со статусом "draft"
        acceptance = Acceptance.objects.filter(creator=user, status='draft').first()

        # Если такой приемки нет, создаем новую
        if not acceptance:
            acceptance = Acceptance.objects.create(
                title='Черновик приемки',
                name='Фамилия Имя Отчество',
                status='draft',
                creator=user
            )

        # Получаем двигатель по ID
        engine = get_object_or_404(Engine, id=id)

        # Проверяем, существует ли связь между приемкой и двигателем
        engine_acceptance_exists = EngineAcceptance.objects.filter(
            acceptance=acceptance, engine=engine
        ).exists()

        # Если связи нет, создаем ее
        if not engine_acceptance_exists:
            EngineAcceptance.objects.create(
                acceptance=acceptance,
                engine=engine,
                accepted='accepted'
            )

        # Перенаправляем пользователя на страницу приемки
        return redirect('acceptance_page', id=acceptance.id)


def delete_acceptance(request, id):
    # Проверяем, что запрос выполнен методом POST
    if request.method == 'POST':
        # Получаем объект приемки для проверки существования
        acceptance = get_object_or_404(Acceptance, id=id)

        # Используем курсоры для выполнения SQL-запроса
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE acceptance SET status = %s WHERE id = %s",
                ['deleted', id]
            )

        return redirect('homepage')

# Данные об услугах
engines_data = [
    {
        'id': 1,
        'title': 'RASA. FJ-44',
        'description': 'Надежный, крепкий двигатель, сконструированный для легкости обслуживания. Уникальный дизайн двигателя позволяет заменять детали пока двигатель установлен на судне.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'image_url': 'http://localhost:9000/rasa/fj-44.png'
    },
    {
        'id': 2,
        'title': 'RASA. CFM-56',
        'description': 'Всемирно известный и универсальный аивадвигатель, предназначен для однопроходных коммерческих лайнеров, а также для различных военных самолетов.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'image_url': 'http://localhost:9000/rasa/cfm-56.png'
    },
    {
        'id': 3,
        'title': 'RASA. BNG-737',
        'description': 'Исключительно надежный, самый продаваемый двигатель в мире за всю историю авиации. На сегодняшний день поставлено более 33 000 двигателей, которыми оснащаются в основном однопроходные коммерческие самолеты Boeing.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'image_url': 'http://localhost:9000/rasa/bng-737.png'
    },
    {
        'id': 4,
        'title': 'RASA. LEAP',
        'description': 'Экологически чистый двигатель, разработанный для решения задачи декарбонизации воздушного транспорта, предлагает операторам самолетов улучшенные показатели расхода топлива и выбросов CO2, выбросов NOx и шума.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'image_url': 'http://localhost:9000/rasa/leap.png'
    },
    {
        'id': 5,
        'title': 'RASA. AP-1',
        'description': 'Легкий и мощный двигатель, разработанный специально для частных летательных судов. Обеспечивает высокую надежность и простоту в обслуживании, идеально подходя для долгосрочной эксплуатации и комфортных тихих полетов.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'image_url': 'http://localhost:9000/rasa/ap-1.png'
    },
    {
        'id': 6,
        'title': 'RASA. CFM-57',
        'description': 'Высокотехнологичный и адаптивный авиадвигатель, младшая модель CFM-56, разработан для обеспечения максимальной производительности и упрощения технического обслуживания, конструкция позволяет легко проводить замену компонентов без снятия двигателя. Идеально подходит для широкого спектра коммерческих и военных летательных аппаратов, обеспечивая надёжность и эффективность при различных условиях эксплуатации.',
        'engine_data': 'ГОСТ Р 52745-2007',
        'image_url': 'http://localhost:9000/rasa/cfm-57.png'
    },

]