import datetime
import pytz

def get_brasilia_time():
    """Retorna data e hora atual no fuso de Brasília no formato dia/mês/ano hora:minuto."""
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(brasilia_tz)
    return now.strftime('%d/%m/%Y %H:%M')
