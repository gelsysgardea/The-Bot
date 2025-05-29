import re
import asyncio
from typing import Optional, Set
from .binance_client import BinanceClient

class ManipulateToken:
    """
    Clase para manipular y validar tokens de Binance Red Packet.
    """
    
    def __init__(self):
        # Patrón para códigos alfanuméricos de exactamente 8 caracteres
        # que no son solo números y no comienzan con BP
        self.token_pattern = re.compile(r'\b(?![Bb][Pp]\w*\b)(?=\w*[A-Za-z])(?=\w*\d)[A-Za-z0-9]{8}\b')
        # Conjunto para almacenar códigos ya procesados
        self.processed_codes: Set[str] = set()
        # Contador de códigos procesados
        self.codes_processed = 0
    
    def clean_text(self, text: str) -> str:
        """
        Limpia el texto eliminando emojis y caracteres especiales.
        """
        # Eliminar emojis
        emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticones
                           u"\U0001F300-\U0001F5FF"  # símbolos y pictogramas
                           u"\U0001F680-\U0001F6FF"  # transporte y símbolos de mapa
                           u"\U0001F1E0-\U0001F1FF"  # banderas (iOS)
                           u"\U00002500-\U00002BEF"  # caracteres chinos comunes
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           u"\U0001f926-\U0001f937"
                           u"\U00010000-\U0010ffff"
                           u"\u2640-\u2642"
                           u"\u2600-\u2B55"
                           u"\u200d"
                           u"\u23cf"
                           u"\u23e9"
                           u"\u231a"
                           u"\ufe0f"  # variantes de emoji
                           u"\u3030"
                           "]+", flags=re.UNICODE)
        
        # Eliminar emojis y caracteres especiales
        clean_text = emoji_pattern.sub(r'', text)
        # Reemplazar múltiples espacios con un solo espacio
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text
    
    def extract_token(self, text: str) -> Optional[str]:
        """
        Extrae un token de un texto.
        
        Args:
            text (str): Texto del que extraer el token
            
        Returns:
            Optional[str]: El token extraído (en mayúsculas) o None si no se encuentra
        """
        if not text or not isinstance(text, str):
            return None
            
        # Limpiar el texto
        clean_text = self.clean_text(text)
        
        # Mostrar información de depuración
        print(f"\n🔍 Analizando texto: {clean_text}")
        
        # Buscar códigos que coincidan con el patrón
        matches = self.token_pattern.findall(clean_text)
        print(f"🔍 Coincidencias encontradas: {matches}")
        
        # Si no hay coincidencias, intentar buscar códigos de 8 caracteres alfanuméricos
        if not matches:
            # Buscar códigos de 8 caracteres alfanuméricos
            potential_codes = re.findall(r'\b([A-Za-z0-9]{8})\b', clean_text)
            print(f"🔍 Códigos potenciales (8 caracteres): {potential_codes}")
            
            # Filtrar códigos que no son solo números y no empiezan con BP
            matches = [
                code for code in potential_codes 
                if not code.isdigit() and not code.upper().startswith('BP')
            ]
            print(f"🔍 Códigos después de filtrar: {matches}")
        
        # Filtrar códigos que ya han sido procesados
        for code in matches:
            # Convertir a mayúsculas para normalizar
            code_upper = code.upper()
            print(f"🔍 Procesando código: {code_upper}")
            
            # Validar que el código tenga exactamente 8 caracteres alfanuméricos
            if len(code_upper) != 8 or not code_upper.isalnum():
                print(f"ℹ️  Código ignorado (longitud o formato incorrecto): {code_upper}")
                continue
                
            # Validar que no sea solo números
            if code_upper.isdigit():
                print(f"ℹ️  Ignorando código numérico: {code_upper}")
                continue
                
            # Validar que no comience con BP
            if code_upper.startswith('BP'):
                print(f"ℹ️  Ignorando código de Binance Pay: {code_upper}")
                continue
            
            # Si el código no ha sido procesado, devolverlo
            if code_upper not in self.processed_codes:
                self.codes_processed += 1
                print(f"✅ Nuevo código encontrado ({self.codes_processed}): {code_upper}")
                self.processed_codes.add(code_upper)
                return code_upper
            else:
                print(f"ℹ️  Código ya procesado anteriormente: {code_upper}")
                
        print("ℹ️  No se encontraron códigos nuevos para procesar")
        return None
    
    def is_valid_token(self, token: str) -> bool:
        """
        Verifica si un token tiene un formato válido.
        
        Args:
            token (str): Token a validar
            
        Returns:
            bool: True si el token es válido, False en caso contrario
        """
        # Verificar que el token coincida con el patrón
        if not bool(self.token_pattern.fullmatch(token)):
            return False
            
        # Verificar que no comience con BP
        if token.upper().startswith('BP'):
            return False
            
        return True
        
    async def process_code(self, code: str) -> dict:
        """
        Procesa un código encontrado y lo canjea en Binance.
        
        Args:
            code (str): Código a procesar
            
        Returns:
            dict: Resultado del canje con las claves 'success' y 'message'
        """
        try:
            if not code or not self.is_valid_token(code):
                return {"success": False, "message": "Código inválido"}
                
            # Normalizar el código a mayúsculas
            code = code.upper()
            
            # Verificar si el código ya fue procesado
            if code in self.processed_codes:
                return {"success": False, "message": "Código ya procesado anteriormente"}
                
            # Crear instancia del cliente de Binance
            binance_client = BinanceClient()
            
            try:
                # Intentar canjear el código
                result = await binance_client.redeem_code(code)
                
                if result.get('success'):
                    # Si el canje fue exitoso, marcar el código como procesado
                    self.processed_codes.add(code)
                    return {"success": True, "message": "Código canjeado exitosamente"}
                else:
                    return {"success": False, "message": result.get('message', 'Error al canjear el código')}
                    
            except Exception as e:
                error_msg = f"Error al procesar el código {code}: {str(e)}"
                print(error_msg)
                return {"success": False, "message": error_msg}
                
            finally:
                # Asegurarse de cerrar la sesión HTTP
                await binance_client.close()
                
        except Exception as e:
            error_msg = f"Error inesperado al procesar el código {code}: {str(e)}"
            print(error_msg)
            return {"success": False, "message": error_msg}
