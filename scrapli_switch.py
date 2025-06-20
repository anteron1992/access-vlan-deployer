from scrapli import Scrapli
from scrapli.exceptions import ScrapliException

from common import get_auth, parse_interface_description, parse_vlan_brief, prepare_data


def device_params(switch):
    """
    Возвращает информацию о устройстве необходимую
    для подключения к свичу через Scrapli c типом
    cisco_iosxe и хостом из переменной switch
    Так как у нас логин/пароль, отключаем
    жестко заданную аутентификацию по ключу
    И говорим что нужно читать ~/.ssh/config
    перед подключением
    """
    return {
        "platform": "cisco_iosxe",
        "host": switch,
        "auth_username": get_auth("USERNAME"),
        "auth_password": get_auth("PASSWORD"),
        "auth_strict_key": False,
        "ssh_config_file": True,
    }


def get_switch_info(switch):
    """
    Возвращает результат выполнения команд выполненных на устройстве
    Если обо что-то ломается в процессе - то сообщаем об ошибке
    """
    try:
        # Подключаемся к устройству
        with Scrapli(**device_params(switch)) as conn:
            # Выполняем команды
            interfaces = conn.send_command("show interface description").result
            vlans = conn.send_command("show vlan brief | exclude unsup").result
            data = {
                "switch": switch,
                "interfaces": parse_interface_description(interfaces),
                "vlans": parse_vlan_brief(vlans),
            }
            return prepare_data(data)
    except ScrapliException as error:
        print(f"Ошибка подключения: {error}")


def deploy_vlan(switch, interfaces, vlans):
    """
    Деплоим VLANы на порты свича
    """
    cmd = []
    # Формируем команды
    for iface, new_vlan in vlans.items():
        # добавляем в список команд, если текущий VLAN не равен новому
        # чтобы не применять уже примененную конфигурацию
        if interfaces[iface]["current_vlan"] != new_vlan:
            cmd.append(f"interface {iface}")
            cmd.append(f"switchport access vlan {new_vlan}")
    # Выполняем команды
    with Scrapli(**device_params(switch)) as conn:
        conn.send_configs(cmd).result