from datetime import datetime

def custom_print(message: str, message_type: str = "INFO") -> None:
    """
    Función personalizada para imprimir mensajes con formato.
    
    Args:
        message (str): Mensaje a imprimir
        message_type (str, optional): Tipo de mensaje (INFO, WARNING, ERROR, SUCCESS). Defaults to "INFO".
    """
    colors = {
        "HEADER": "\033[95m",
        "BLUE": "\033[94m",
        "CYAN": "\033[96m",
        "GREEN": "\033[92m",
        "WARNING": "\033[93m",
        "RED": "\033[91m",
        "ENDC": "\033[0m",
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m"
    }
    
    # Seleccionar color basado en el tipo de mensaje
    color = ""
    if message_type == "INFO":
        color = colors["CYAN"]
    elif message_type == "WARNING":
        color = colors["WARNING"]
    elif message_type == "ERROR":
        color = colors["RED"]
    elif message_type == "SUCCESS":
        color = colors["GREEN"]
    else:
        color = colors["ENDC"]
    
    # Obtener la fecha y hora actual
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Imprimir el mensaje formateado
    print(f"{colors['BOLD']}[{now}]{colors['ENDC']} {color}[{message_type}]{colors['ENDC']} {message}")
