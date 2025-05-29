from telethon import TelegramClient, events

from source import Config
from source import custom_print
from lib.manipulator import ManipulateToken


class BaseClient:
    def __init__(self):
        self.config: Config = Config()
        self.client: TelegramClient = TelegramClient(
            self.config.CLIENT_NAME, self.config.API_ID, self.config.API_HASH
        )
        self.manipulator = ManipulateToken()
        self.selected_chats = set()
        self.setup_event_handler()
        
    async def list_chats(self):
        """Lista todos los chats/grupos disponibles"""
        print("\n📋 Listando chats disponibles...")
        dialogs = await self.client.get_dialogs()
        
        print("\n💬 Chats disponibles:")
        print("-" * 50)
        for i, dialog in enumerate(dialogs, 1):
            chat = dialog.entity
            chat_id = chat.id if hasattr(chat, 'id') else None
            chat_title = getattr(chat, 'title', 'Chat privado')
            print(f"{i}. {chat_title} (ID: {chat_id})")
        
        return dialogs
        
    async def select_chats(self):
        """Permite al usuario seleccionar los chats a monitorear"""
        dialogs = await self.list_chats()
        selected = input("\n🔢 Ingresa los números de los chats que deseas monitorear (separados por comas): ")
        
        selected_indices = [int(idx.strip()) - 1 for idx in selected.split(',') if idx.strip().isdigit()]
        self.selected_chats = set()
        
        for idx in selected_indices:
            if 0 <= idx < len(dialogs):
                chat = dialogs[idx].entity
                chat_id = chat.id if hasattr(chat, 'id') else None
                if chat_id:
                    self.selected_chats.add(chat_id)
                    chat_title = getattr(chat, 'title', 'Chat privado')
                    print(f"✅ Seleccionado: {chat_title} (ID: {chat_id})")

    def setup_event_handler(self):
        @self.client.on(events.NewMessage())
        async def _(event: events.NewMessage.Event):
            try:
                # Obtener información del chat
                chat = await event.get_chat()
                chat_id = event.chat_id
                chat_name = getattr(chat, 'title', 'Chat privado')
                
                # Si no hay chats seleccionados, seleccionarlos
                if not hasattr(self, 'selected_chats') or not self.selected_chats:
                    print("\n⚠️ No hay chats seleccionados. Por favor selecciona los chats a monitorear.")
                    await self.select_chats()
                    return
                
                # Verificar si el mensaje viene de un chat seleccionado
                if chat_id not in self.selected_chats:
                    #print(f"\nℹ️ Mensaje ignorado (chat no seleccionado): {chat_name} (ID: {chat_id})")
                    return
                
                # Mostrar información del mensaje recibido
                print(f"\n📨 Mensaje recibido de {chat_name} (ID: {chat_id})")
                print(f"📝 Contenido: {event.raw_text}")
                
                # Procesar el mensaje para extraer códigos
                code = self.manipulator.extract_token(event.raw_text)
                if code:
                    print(f"🔑 Código detectado: {code}")
                    # Intentar canjear el código
                    result = await self.manipulator.process_code(code)
                    if result and result.get('success'):
                        print(f"✅ Código canjeado exitosamente: {code}")
                    else:
                        error_msg = result.get('message', 'Error desconocido') if result else 'Error al procesar el código'
                        print(f"❌ Error al canjear el código {code}: {error_msg}")
                
                # Mostrar información detallada del mensaje
                custom_print("\n" + "="*50, "DEBUG")
                custom_print(f"📨 NUEVO MENSAJE RECIBIDO", "DEBUG")
                custom_print(f"💬 Chat: {chat_name} (ID: {chat_id})", "DEBUG")
                
                # Obtener el texto del mensaje
                message_text = event.raw_text.strip()
                custom_print(f"📝 Contenido: {message_text}", "DEBUG")
                
                # Verificar si el chat está en la lista de CHATS
                if chat_id not in self.config.CHATS:
                    custom_print(f"ℹ️  Ignorando mensaje de chat no configurado (ID: {chat_id})", "INFO")
                    custom_print(f"ℹ️  CHATS configurados: {self.config.CHATS}", "DEBUG")
                    return
                
                # Extraer el código del mensaje
                custom_print("🔍 Buscando códigos en el mensaje...", "DEBUG")
                code = self.manipulator.extract_token(message_text)
                
                if code:
                    custom_print(f"✅ CÓDIGO ENCONTRADO: {code}", "SUCCESS")
                    custom_print(f"🔗 URL de canje: https://www.binance.com/es/my/wallet/account/payment/cryptobox", "INFO")
                    
                    # Procesar el código de manera asíncrona
                    custom_print("🔄 Intentando canjear el código...", "INFO")
                    result = await self.manipulator.process_code(code)
                    
                    # Mostrar resultado del canje
                    if result and result.get('success'):
                        custom_print("🎉 ¡CÓDIGO CANJEADO EXITOSAMENTE EN BINANCE!", "SUCCESS")
                    elif result:
                        custom_print(f"⚠️  {result.get('message', 'Error desconocido')}", "WARNING")
                    
                    # Mostrar respuesta completa para depuración
                    custom_print(f"📄 Respuesta completa: {result}", "DEBUG")
                else:
                    custom_print("ℹ️  No se encontró ningún código válido en el mensaje", "INFO")
                
                custom_print("="*50, "DEBUG")
                
            except Exception as e:
                import traceback
                error_msg = f"❌ ERROR AL PROCESAR MENSAJE: {str(e)}\n{traceback.format_exc()}"
                custom_print(error_msg, "ERROR")

    async def start(self):
        """Inicia el cliente de Telegram de manera asíncrona."""
        custom_print("Iniciando el cliente de Telegram...", "info")
        
        try:
            # Verificar si ya hay una sesión guardada
            custom_print("Conectando con los servidores de Telegram...", "info")
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                custom_print("\n=== MODO AUTENTICACIÓN ===", "warning")
                custom_print(f"No se encontró una sesión activa. Se enviará un código al número: {self.config.PHONE}", "warning")
                
                try:
                    # Enviar código de autenticación
                    custom_print("\nEnviando código de verificación a Telegram...", "info")
                    sent_code = await self.client.send_code_request(self.config.PHONE, force_sms=True)
                    custom_print("¡Código enviado! Revisa tus mensajes de Telegram.", "success")
                    
                    # Mejorar la entrada del código de verificación
                    while True:
                        try:
                            print("\n" + "="*50)
                            code = input("\n📱 Por favor, ingresa el código de 5 dígitos que recibiste en Telegram\n(escribe 'salir' para cancelar): ")
                            
                            if code.lower() == 'salir':
                                custom_print("\n❌ Autenticación cancelada por el usuario.", "warning")
                                return False
                                
                            if code.isdigit() and len(code) == 5:
                                custom_print(f"\n🔑 Verificando código: {'•' * len(code)}", "info")
                                await self.client.sign_in(self.config.PHONE, code)
                                custom_print("\n✅ ¡Autenticación exitosa!", "success")
                                break
                            else:
                                custom_print("\n❌ Código inválido. Por favor, ingresa exactamente 5 dígitos numéricos.", "error")
                        except Exception as e:
                            custom_print(f"\n⚠️ Error al verificar el código: {str(e)}", "error")
                            if "PHONE_CODE_INVALID" in str(e):
                                custom_print("El código es incorrecto o ha expirado. Por favor, verifica y vuelve a intentar.", "error")
                            elif "SESSION_PASSWORD_NEEDED" in str(e):
                                custom_print("Se requiere verificación en dos pasos. Por favor, ingresa tu contraseña de verificación en dos pasos.", "error")
                                password = input("Contraseña de verificación en dos pasos: ")
                                await self.client.sign_in(password=password)
                                break
                            else:
                                custom_print("Error desconocido. Por favor, inténtalo de nuevo.", "error")
                except Exception as e:
                    custom_print(f"\n❌ Error al enviar el código de verificación: {str(e)}", "error")
                    return False
            else:
                custom_print("\n✅ Sesión encontrada. Iniciando...", "success")
                
            custom_print("Telethon iniciado correctamente. Esperando mensajes...", "info")
            return True
            
        except Exception as e:
            custom_print(f"Error al iniciar el cliente de Telegram: {str(e)}", "error")
            return False
