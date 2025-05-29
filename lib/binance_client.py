import httpx
import asyncio
import json
import random
import time
from typing import Dict, Any, Optional
from source.config import Config
from source.custom_print import custom_print

class BinanceClient:
    def __init__(self):
        self.config = Config()
        self.base_url = "https://www.binance.com/bapi/"
        self.session = None
        self._init_session()
    
    def _init_session(self):
        """Inicializa la sesión HTTP con los headers correctos"""
        self.session = httpx.AsyncClient(
            headers=self.config.HEADERS,
            timeout=30.0,
            http2=True
        )
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Método genérico para realizar peticiones HTTP"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Añadir delay aleatorio para parecer más humano
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        try:
            # Realizar la petición
            response = await self.session.request(
                method=method,
                url=url,
                **kwargs
            )
            
            # Intentar parsear la respuesta como JSON
            try:
                result = response.json()
            except json.JSONDecodeError:
                result = {"message": response.text, "status_code": response.status_code}
            
            # Registrar la respuesta para depuración
            custom_print(f"🔁 Respuesta de Binance ({response.status_code}): {json.dumps(result, indent=2)}", "DEBUG")
            
            # Verificar si la respuesta indica que el token ha expirado
            if response.status_code == 403 and 'token' in str(result).lower():
                custom_print("⚠️  Token de sesión expirado. Es necesario actualizar los tokens en la configuración.", "WARNING")
                
            return {
                "success": response.status_code == 200 and result.get('success', False),
                "status_code": response.status_code,
                "data": result,
                "message": result.get('message', 'Respuesta recibida')
            }
            
        except httpx.TimeoutException as e:
            error_msg = f"⏱️  Tiempo de espera agotado: {str(e)}"
            custom_print(error_msg, "ERROR")
            return {"success": False, "message": error_msg}
            
        except Exception as e:
            error_msg = f"❌ Error en la petición: {str(e)}"
            custom_print(error_msg, "ERROR")
            return {"success": False, "message": error_msg}
    
    async def redeem_code(self, code: str) -> Dict[str, Any]:
        """
        Canjea un código en Binance usando el método grabv2.
        
        Args:
            code (str): Código a canjear (debe tener 8 caracteres alfanuméricos)
            
        Returns:
            Dict[str, Any]: {
                'success': bool,
                'message': str,
                'data': dict,
                'status_code': int
            }
        """
        if not code or len(code) != 8 or not code.isalnum():
            return {
                "success": False,
                "message": f"Código inválido: {code}. Debe tener exactamente 8 caracteres alfanuméricos.",
                "data": None,
                "status_code": 400
            }
        
        custom_print(f"🔄 Intentando canjear código: {code}", "INFO")
        
        # Preparar el payload
        payload = {
            "code": code.upper(),
            "clientType": "web"
        }
        
        # Realizar la petición
        result = await self._make_request(
            method="POST",
            endpoint="pay/v1/private/cryptobox/grabv2",
            json=payload
        )
        
        # Interpretar la respuesta
        if result.get('success'):
            custom_print(f"✅ ¡Código {code} canjeado con éxito!", "SUCCESS")
            result['message'] = f"Código {code} canjeado con éxito"
        else:
            error_msg = result.get('message', 'Error desconocido al canjear el código')
            custom_print(f"❌ Error al canjear el código {code}: {error_msg}", "ERROR")
            
        return result
    
    async def close(self):
        """Cierra la sesión HTTP de manera segura"""
        if self.session:
            try:
                await self.session.aclose()
                custom_print("🔒 Sesión HTTP cerrada correctamente", "INFO")
            except Exception as e:
                custom_print(f"⚠️  Error al cerrar la sesión HTTP: {str(e)}", "WARNING")
