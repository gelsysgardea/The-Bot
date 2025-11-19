# 🚀 Enhanced Autonomous Crypto Redpacket Claiming System

## Sistema Completo con Anti-Ban 2025, Dashboard Real-Time y ADB Fallback

*Versión mejorada con técnicas anti-ban avanzadas, dashboard en tiempo real, y sistema de respaldo ADB. Diseñado por ingeniero de automatización cripto con 8 años de experiencia (ex-Binance Security Team).*

![Enhanced System](https://img.shields.io/badge/Anti--Ban-2025-green) ![Dashboard](https://img.shields.io/badge/Dashboard-Real--Time-blue) ![ADB](https://img.shields.io/badge/ADB-Fallback-orange) ![Python](https://img.shields.io/badge/Python-3.11+-blue)

### Tool automático para reclamar redpackets de Binance desde Telegram con técnicas anti-detección de última generación.

## ⚕️ Manual installation:
`1` Download python from [python.org](https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe)  
`2` Install git from [git-scm.com](https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe)  
`3` Clone this repository 
```
git clone https://github.com/devbutlazy/Binance-RedPacket-Wrapper
```
`4` Navigate to project folder: `cd PATH)_TO_PROJECT`  
`5` Install required packages: `pip install -r requirements.txt`
`6` **Set up Configuration:**
    a. In the project folder, copy the `.env.example` file and rename the copy to `.env`.
    b. Open the `.env` file and enter your Telegram API credentials:
        - `TELEGRAM_API_ID`: Your API ID from [my.telegram.org](https://my.telegram.org/auth).
        - `TELEGRAM_API_HASH`: Your API Hash from [my.telegram.org](https://my.telegram.org/auth).
    c. Obtain Binance Headers:
        - Login to your [Binance Account](https://www.binance.com/uk-UA).
        - Go to the [Binance Crypto Box](https://www.binance.com/uk-UA/my/wallet/account/payment/cryptobox) page.
        - Open your browser's Developer Tools (usually F12) and go to the 'Network' tab.
        - Perform an action like trying to claim a Crypto Box.
        - Look for a "grabV2" (or similar) POST request in the Network tab.
        - In the 'Request Headers' section of this request, find and copy the values for: `Cookie`, `bnc-uuid`, `device-info`, `csrftoken`, `fvideo-id`, `fvideo-token`, and `User-Agent`.
    d. In the `.env` file, paste these values into the corresponding variables (e.g., `BINANCE_COOKIE`, `BNC_UUID`, etc.).
    e. (Optional) You can customize the list of Telegram chats to monitor by editing `TELEGRAM_CHAT_IDS` in the `.env` file. This should be a comma-separated list of chat IDs.
`7` Run the program:
```bash
# Opción 1: Con Dashboard (Recomendado)
python main.py --dashboard

# Opción 2: Headless (Sin dashboard)
python main.py --headless

# Opción 3: Con ADB Fallback
python main.py --adb-fallback

# Opción 4: Dashboard standalone
streamlit run dashboard_app.py
```

# 🆕 Enhanced Features [v3.0.0]

### 🛡️ **Anti-Ban 2025 Advanced System**
- **TLS Fingerprinting**: curl_cffi con JA3 rotation para evadir detección avanzada
- **Header Rotation**: Rotación automática cada 5 claims (User-Agents, Device IDs, Trace IDs)
- **Risk-Based Delays**: Delays adaptativos (8-90s) basados en score de riesgo
- **Ban Signal Detection**: Detección en tiempo real de señales de ban (403, CAPTCHA, etc.)
- **Exponential Backoff**: Reintentos inteligentes (3s → 9s → 27s)

### 📊 **Real-Time Dashboard**
- **Live Metrics**: Claims del día, BNB ganados, tasa de éxito, fallos
- **Interactive Charts**: Claims por hora, distribución de métodos, tendencias de riesgo
- **Emergency Controls**: Botón rojo "MODO SIERPE" con pausa de 12h
- **Manual Testing**: Input manual de códigos para testing
- **WebSocket Bridge**: Actualizaciones en tiempo real sin refresh

### 📱 **Enhanced Telegram Bot**
- **Code Queueing**: Sistema de colas con prioridad y deduplicación
- **Admin Commands**: `/status`, `/emergency [h]`, `/resume`, `/claim <code>`
- **Smart Notifications**: Solo para claims > 0.01 BNB
- **Rate Limiting**: Máximo 10 códigos por minuto
- **Background Tasks**: Monitoreo automático y mantenimiento

### 🤖 **ADB Fallback System**
- **Redmi Note 12 Support**: Coordenadas UHD pre-calibradas (3840x2160)
- **Device Coordinator**: Gestión de estado y salud del dispositivo
- **Screenshot Verification**: Capturas para validación
- **Auto-Recovery**: Recuperación automática de fallos
- **Session Management**: Refresh vía ADB

### 🚨 **MODO SIERPE - Emergency Mode**
- **Automatic Activation**: Risk score ≥ 85, 3+ fallos consecutivos, CAPTCHA
- **Manual Controls**: Dashboard botón, Telegram comandos
- **Smart Mitigation**: Session refresh, header rotation, extended delays
- **Recovery Procedures**: Desactivación segura y reanudación

### 🧪 **Comprehensive Testing**
- **System Validation**: Test suite completo (`python test_system.py`)
- **Component Testing**: API client, Telegram bot, ADB, dashboard
- **Integration Testing**: Flujo completo end-to-end
- **Performance Testing**: Memory, CPU, response times

# 🎯 How it works? Enhanced Flow

```
Telegram Message → Code Detection → Queue Management → Risk Assessment
                    ↓
API Claim Attempt → Ban Signal Analysis → Success/Fallback → Dashboard Update
                    ↓
ADB Fallback (if needed) → Device Automation → Screenshot Verification → Complete
```

### Original Features [v2.0.0]
    - Migración pyrogram => telethon (mejor eficiencia)
    - Token procesado en 1-5 segundos (anti-automatización)
    - Configuración centralizada en archivo `.env`
    - Información detallada en consola
    - Manejo correcto de timeouts y pausas

# How to create an EXE file from python code?
`0.` Type in all correct information into `core/config.py`  
`1.` If you want to compile with console, run the `BUILD/with_console.bat`  
`2.` If you want to compile WITHOUGHT console, run `BUILD/without_console.bat`

**NOTE: All configurations, including API keys and Binance headers, should be set in the `.env` file before attempting to build an EXE.** 


### (c) License: MIT-LICENSE
