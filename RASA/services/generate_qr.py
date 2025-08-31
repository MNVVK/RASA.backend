import segno
import base64
from io import BytesIO


def generate_acceptance_qr(acceptance, engine_acceptances):
    """
    Генерация QR-кода для Приёмки.

    :param acceptance: объект модели Acceptance
    :param engine_acceptances: список объектов модели EngineAcceptance
    :return: base64 строка с изображением QR-кода
    """

    # Формируем текст для QR-кода
    info = f"Приёмка №{acceptance.id}\nНазвание: {acceptance.title}\nСоздатель: {acceptance.creator}\n\n"

    # Информация о двигателях в приёмке
    engines_summary = {}
    for engine_acceptance in engine_acceptances:
        engine = engine_acceptance.engine
        status = "✅ Принят" if engine_acceptance.accepted == "accepted" else "❌ Отклонён"

        if engine.title not in engines_summary:
            engines_summary[engine.title] = {"count": 0, "status": status}

        engines_summary[engine.title]["count"] += 1

    total_accepted = 0
    for engine_name, data in engines_summary.items():
        info += f"{engine_name} - {data['count']} шт. ({data['status']})\n"
        if data["status"] == "✅ Принят":
            total_accepted += data["count"]

    info += f"\nВсего принятых двигателей: {total_accepted}\n"

    # Дата формирования приёмки
    formation_date = acceptance.formation_date.strftime(
        '%Y-%m-%d %H:%M:%S') if acceptance.formation_date else "Не сформирована"
    info += f"\nДата формирования: {formation_date}"

    # Генерация QR-кода
    qr = segno.make(info)
    buffer = BytesIO()
    qr.save(buffer, kind='png')
    buffer.seek(0)

    # Конвертация изображения в base64
    qr_image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return qr_image_base64
