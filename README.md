# Binance CryptoBox Wrapper
![binance_wrapper](https://github.com/user-attachments/assets/e0615cb7-43e1-457f-8b68-9262a9147920)

### A tool to wrap cryptoboxes from Telegram channels automatically.

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
```
python main.py
```

# How it works? What are the features?

### [v2.0.0]
    - Rewritten to a new user-bot lib: migration pyrogram => telethon (for better efficiency)
    
    - The token is passed to Binance API within 1-5 seconds (to prevent input automation). 

    - Centralized configuration using an `.env` file for API keys, Binance headers, and bot settings.

    - The console gives information about found crypto-tokens, amount and valid-state.

    - If there is a timeout, the programm will CORRECTLY pause all the proccesses.

# How to create an EXE file from python code?
`0.` Type in all correct information into `core/config.py`  
`1.` If you want to compile with console, run the `BUILD/with_console.bat`  
`2.` If you want to compile WITHOUGHT console, run `BUILD/without_console.bat`

**NOTE: All configurations, including API keys and Binance headers, should be set in the `.env` file before attempting to build an EXE.** 


### (c) License: MIT-LICENSE
