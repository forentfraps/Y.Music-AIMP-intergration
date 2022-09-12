import requests
from fake_headers import Headers
import json
import time
import xmltodict
from hashlib import md5
import browser_cookie3
from pywinauto import Desktop
import psutil
import win32process
from os import listdir, mkdir
from os.path import isfile, join, exists
import xml
from multiprocessing import Pool
from itertools import repeat
import threading
import os
import shutil
from selenium import webdriver 
from selenium.webdriver.common.by import By
import pyaimp
import sys
import snatch

def get_cur_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable) + f'{os.sep}Y{os.sep}'
    elif __file__:
        return os.path.dirname(__file__) + f'{os.sep}Y{os.sep}'
    return False
class YM:
    def __init__(self, debug = False):
        self.s = requests.Session()
        self.PATH = get_cur_path()
        self.browser = None
        self.progress = 0
        self.progress_type = None
        self.check_ex_files() 
        self.token = self.get_token()
        self.uid = self._get_uid()
        if not debug:
            self.thr_bulk_download_daily()
            self.thr_bulk_download_like()
        
    def check_ex_files(self):
        """
        Checks for required files and directories, useful on the initial start\n
        Creates ./Y directory
        """
        if not exists(self.PATH):
            mkdir(self.PATH)
        if not exists(f'{self.PATH}daily'):
            mkdir(f'{self.PATH}daily')
        if not exists(f'{self.PATH}likes'):
            mkdir(f'{self.PATH}likes')
        if not exists(f'{self.PATH}radio'):
            mkdir(f'{self.PATH}radio')
        if not exists(f'{self.PATH}daily_ups.txt'):
            with open(f'{self.PATH}daily_ups.txt','w') as f:
                f.write("0")
        
    def _get_browser(self):
        """
        Ckecks opened windows for opened browsers from the supported list (that list comes from browser_cookie3 limitations)
        sets self.browser to discovered browser
        """
        br_list = ["chrome","firefox","opera","edge","chromium","brave","vivaldi"]
        windows = Desktop(backend="uia").windows()
        c = [psutil.Process(win32process.GetWindowThreadProcessId(w.handle)[1]).name() for w in windows]
        data = list(set(filter(bool,map(lambda x:  x[:-4] if any([br in x.lower() for br in br_list]) else False, c))))
        data.sort()
        self.browser = data[0]
    
    def grab_cookies(self):
        """
        Steals cookies (domain yandex.ru only), and injects them into requests.session
        """
        if not self.browser:
            self._get_browser()
        match self.browser:
            case "chrome":
                cj = browser_cookie3.chrome(domain_name='yandex.ru')
            case "firefox":
                cj = browser_cookie3.firefox(domain_name='yandex.ru')
            case "opera":
                cj = browser_cookie3.opera(domain_name='yandex.ru')
            case "edge":
                cj = browser_cookie3.edge(domain_name='yandex.ru')
            case "chromium":
                cj = browser_cookie3.chromium(domain_name='yandex.ru')
            case "brave":
                cj = browser_cookie3.brave(domain_name='yandex.ru')
            case "vivaldi":
                cj = browser_cookie3.vivaldi(domain_name='yandex.ru')
        for cookie in cj:
            self.s.cookies.set_cookie(cookie)
    def get_token(self):
        """
        Grabs the needed api token, and saves it, eliminating the need to steal cookies every time
        """
        if exists(f"{self.PATH}token.txt"):
            with open(f"{self.PATH}token.txt", 'r') as f:
                self.token = f.read()
            return
        self.grab_cookies()
        prompt = "https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d"
        resp = self.s.get(prompt, allow_redirects=True)
        sep1 = "#access_token="
        sep2 = "&"
        try:
            self.token = resp.text.split(sep1)[1].split(sep2)[0]
        except Exception as e:
            print(f"Make sure you logged in and accepted the terms at https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d\n\nError = {e}")
            input('awaiting input ...')
            exit()
        #reset session to avoid heavy requests
        self.s = requests.Session()
        with open(f'{self.PATH}token.txt', "w") as f:
            f.write(self.token)
        
    def get(self, prompt, auth = True, params = None):
        """
        Thats basically a requests.get() wrapper with api token authorization
        """
        if not self.token and auth:
            self.get_token()
        headers=Headers(browser="chrome", os="win", headers=True ).generate()
        if auth:
            headers.update({'Authorization': f'OAuth {self.token}'})

        return requests.get(prompt, headers = headers, params = params)
    def post(self, prompt, arg, auth = True):
        """
        A requests.post() wrapper with authorization
        """
        if not self.token and auth:
            self.get_token()
        headers=Headers(browser="chrome", os="win", headers=True ).generate()
        if auth:
            headers.update({'Authorization': f'OAuth {self.token}'})

        return requests.post(prompt,arg,  headers = headers)
    def info(self, type, id):
        """
        Usualy gets information about tracks, but has plenty other uses
        
        Input -> type: str  == type of objest\n
        id: int | str == id of that object\n
        Output -> response: dict
        """
        prompt = f"https://api.music.yandex.net/{type}s/{id}"
        try:
            return self.get(prompt).json()
        except:
            raise TypeError
    def get_track_info(self, trackId):
        """
        Gets tracks name and artist\n
        Input -> trackId: str | int\n
        Returns name: str, artist: str
        """
        track_inf = self.info("track", trackId)['result'][0]
        name = track_inf['title']
        table = dict.fromkeys(map(ord, '\/.*?:<>'), None) #parsing 
        name = name.translate(table)
        artist = ""
        if len(track_inf['artists']) > 0:
            artist = track_inf['artists'][0]['name']
        return name, artist
    def download_link(self, trackId):
        if not self.token:
            self.get_token()
        try:
            name, artist = self.get_track_info(trackId)
            prompt = f"https://api.music.yandex.net/tracks/{trackId}/download-info"

            req = self.get(prompt)
            data = json.loads(req.text)
            if 'error' in data.keys():
                print('Error in data keys, Exception in y.download_link, #L164')
                return
            dil = data['result'][0]['downloadInfoUrl']
            #try except loop is here, because of yandex api returning total garbage some times
            try:
                req = xmltodict.parse(self.get(dil).content.decode('utf-8', 'ignore'))
            except xml.parsers.expat.ExpatError:
                time.sleep(1)
                print('Error with xml, Exception in y.download_link, #L164')
                return self.download_link(trackId)
            info = req['download-info'] #gets download information from the api
            sign = md5(('XGRlBW9FXlekgbPrRHuSiA' + info['path'][1::] + info['s']).encode('utf-8')).hexdigest() #reverse engineered stuff, nothing to say here
            link = f"https://{info['host']}/get-mp3/{sign}/{info['ts']}{info['path']}"
            return link
        except Exception as e:
            time.sleep(0.05)
            print(e, 'Exception in y.downoad_link #L164')
            return self.download_link(self, trackId)
    def download(self, trackId, dir: str):
        """
        Reverse engineered track downloader
        
        Input -> trackId: int | str \n
        dir: str ==  directory to where the file will be downloaded
        """
        if not self.token:
            self.get_token()
        try:
            name, artist = self.get_track_info(trackId)
            prompt = f"https://api.music.yandex.net/tracks/{trackId}/download-info"

            req = self.get(prompt)
            data = json.loads(req.text)
            if 'error' in data.keys():
                return
            dil = data['result'][0]['downloadInfoUrl']
            #try except loop is here, because of yandex api returning total garbage some times
            try:
                req = xmltodict.parse(self.get(dil).content.decode('utf-8', 'ignore'))
            except xml.parsers.expat.ExpatError:
                time.sleep(1)
                return self.download(trackId, dir)
            info = req['download-info'] #gets download information from the api
            sign = md5(('XGRlBW9FXlekgbPrRHuSiA' + info['path'][1::] + info['s']).encode('utf-8')).hexdigest() #reverse engineered stuff, nothing to say here
            link = f"https://{info['host']}/get-mp3/{sign}/{info['ts']}{info['path']}"
            with open(f"{dir}/{name}_{artist}_{trackId}.mp3", "wb") as f:
                f.write(self.get(link).content)
        except Exception as e:
            print(f"error with {trackId}, exc = {e}")
    def post_radio(self,prompt,  auth = True, params = None, json = None):
        """
        Different requests.post() wrapper used in radio(aka rotor) purposes
        """
        if not self.token and auth:
            self.get_token()
        headers=Headers(browser="chrome", os="win", headers=True ).generate()
        return requests.post(prompt,params = params,json = json,  headers = headers)
    
    def _get_uid(self):
        """
        Gets users UID, needed for feetching daily and liked playlists
        """
        if not self.token:
            self.get_token()
        prompt = f"https://api.music.yandex.net/account/status"
        resp = json.loads(self.get(prompt).text)
        self.uid = resp['result']['account']['uid']
        
    def like(self, trackId: int, remove = False):
        """
        Likes the current track in yandex music and downloades it to the ./Y/likes folder\n
        Input -> trackId: str | int\n
        remove: bool == If True will remove the like instead
        """
        if not self.uid:
            self._get_uid()
        action = 'remove' if remove else 'add-multiple'
        link = f'https://api.music.yandex.net/users/{self.uid}/likes/tracks/{action}'
        self.post(link, {"track-ids": trackId})
        if not remove:
            
            threading.Thread(target = self.download, args = (trackId, f"{self.PATH}likes")).start()
        
        
    def fetch_daily_playlist(self):
        """
        Fetches daily and for user generated playlists such as premiere for example\n
        Returns -> a list of [owner:kind] , needed for later track fetching
        """
        
        if not self.uid:
            self._get_uid()
        url = f'https://api.music.yandex.net/users/{self.uid}/likes/playlists'
        resp = self.get(url)
        data = json.loads(resp.text)['result']
        
        #return [p['playlist']for p in data]
        return [[p['playlist']['owner']['uid'],p['playlist']['kind']] for p in data]
    def playlist_info(self, owner, puid):
        """
        Gets playlist information, mostly used for track fetching\n
        Input -> owner: int\n
        puid: int\n
        Returns a response: dict
        """
        prompt = f"https://api.music.yandex.net/users/{owner}/playlists/{puid}"
        return self.get(prompt).json()

    def fetch_like_tracks(self):
        """
        Fetches liked tracks\n
        Returns a list of trackId\n
        NOTE: it probably wont download user added tracks, however, the odds could be on your side :-)
        """
        if not self.uid:
            self._get_uid()
        url = f'https://api.music.yandex.net/users/{self.uid}/likes/tracks'
        resp = self.get(url)
        data = json.loads(resp.text)['result']['library']
        return [t['id']  for t in data['tracks']]
    
    def tracks_from_playlists(self, owner, puid):
        """
        Fetches tracks from a given playlist
        Input -> owner: int\n
        puid: int\n
        Returns a list of trackId\n
        """
        if not self.uid:
            self._get_uid()
        p_inf = self.playlist_info(owner, puid)
        return [track['id'] for track in p_inf['result']['tracks']]
    
    def fetch_daily_tracks(self):
        """
        Fetches tracks from daily playlist\n
        Returns a list of trackId
        """
        plays = self.fetch_daily_playlist()
        trackIds = []
        c = [self.tracks_from_playlists(owner,kind) for owner, kind in plays]
        for tracklist in c:
            trackIds += tracklist
        return trackIds
    

    def bulk_download(self, trackIds, dir):
        """
        Mulitprocessing implementation for downloading a list of trackId\n
        Input -> trackIds: list[int]\n
        dir: str\n
        """
        self.progress_type = "Downloading" #used for a cool progress bar in main.pyw
        pool = Pool(8)
        pool.starmap(self.download, zip(trackIds, repeat(dir)))
        pool.close()
        pool.join()
        self.progress_type = None
    def bulk_download_daily(self):
        """
        Downloads daily tracks
        """
        tracks = self.fetch_daily_tracks()
        dir = f"{self.PATH}daily"
        files = [f for f in listdir(dir) if isfile(join(dir, f))]
        print(list(map(lambda x: int(x.split("_")[-1][:-4]) in tracks, files)).count(True))
        print(len(tracks))
        if not all(list(map(lambda x: int(x.split("_")[-1][:-4]) in tracks, files))):
    
            for filename in listdir(dir):
                file_path = os.path.join(dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
                    
            self.bulk_download(tracks, dir)
        print("done")
    def thr_bulk_download_daily(self):
        """
        Creates a separate thread for downloading daily (used for main menu to function, while tracks are fetching, downloading, etc..)
        """
        t = threading.Thread(name='daily download', target=self.bulk_download_daily, daemon = True)
        t.start()
    def bulk_download_like(self):
        """
        Downloads liked tracks
        """
        tracks =  self.fetch_like_tracks()
        dir = f"{self.PATH}likes"
        
        files = [f for f in listdir(dir) if isfile(join(dir, f))]
        trackIds = list(filter(bool, [trackId if trackId not in tracks else 0 for trackId in list(map(lambda x: x.split("_")[-1][:-4], files))]))
        self.bulk_download(trackIds, dir)
        
        print("done")
    def thr_bulk_download_like(self):
        """
        Creates a separate thread for downloading liked (used for main menu to function, while tracks are fetching, downloading, etc..)
        """
        t = threading.Thread(name='like download', target=self.bulk_download_like, daemon = True)
        t.start()
        print("Started the thr, back to main")
    def get_track_len(self, trackId):
        """
        Gets track duration in MS
        Input -> trackId: str | int\n
        Returns str
        """
        return self.info('track', trackId)['result'][0]['durationMs']
    def get_wave_info(self):
        """
        Cosmetic feature
        """
        return self.get(f'https://api.music.yandex.net/rotor/station/user:onyourwave/info').json()
    def update_radio(self, type_, trackId = None, from_ = None, batch_id = None, total_played_seconds = None):
        """
        Sends a feedback to music.yandex.ru, needed for a better radio track fetching
        """
        data = {'type': type_, 'timestamp': time.time()}
        if batch_id:
            params = {'batch-id': batch_id}

        if trackId:
            data.update({'trackId': trackId})

        if from_:
            data.update({'from': from_})

        if total_played_seconds:
            data.update({'totalPlayedSeconds': total_played_seconds})

        return self.post_radio("https://api.music.yandex.net/rotor/station/user:onyourwave/feedback", params=params, json=data)
    def get_radio(self, queue = None):
        """
        Gets first 5 radio tracks, and batchId\n
        Input -> queue (optional) : list[trackId] == needed to avoid track repetition and algorithm enchancements\n
        Returns some tracks: list[trackId] (either a prolonged queue or new 5 tracks), batchId : str
        """
        url = f'https://api.music.yandex.net/rotor/station/user:onyourwave/tracks'
        params = {'settings2': str(True)}
        if queue:
            params.update({'queue': queue})
        resp = self.get(url,params = params)
        return [track['track']['id'] for track in resp.json()['result']['sequence']], resp.json()['result']['batchId']

    def start_radio(self):
        """
        Sends a radio started feedback\n
        Returns list[trackId], batchId
        """
        from_ = f'mobile-radio-user-{self.uid}'
        trackIds, batchId = self.get_radio()
        self.update_radio('radioStarted', from_ = from_, batch_id = batchId)
        return trackIds, batchId
    def fake_listen(self, trackId, batchId):
        """
        Sends a fake feedback about listening the last track\n
        It is needed for track quolity enchancement
        """
        self.update_radio('trackStarted', trackId = trackId, batch_id = batchId)
        track_dur = self.get_track_len(trackId)
        self.update_radio('trackFinished', trackId = trackId, batch_id = batchId, total_played_seconds=track_dur)
    def fetch_radio(self):
        """
        Fetches 100 radio tracks\n
        Returns list[trackId]
        """
        trackIds, batchId = self.start_radio()
        lst_listened = trackIds[-1]
        self.progress_type = "Fetching tracks"
        while len(trackIds) < 100:
            self.progress= len(trackIds)
            self.fake_listen(lst_listened, batchId)
            tmp_tracks, batchId = self.get_radio(queue = trackIds)
            lst_listened = tmp_tracks[-1]
            trackIds = list(set(trackIds + tmp_tracks))
        self.progress = 0
        return trackIds
    def bulk_radio(self):
        """
        Downloads radio tracks
        """
        trackIds = self.fetch_radio()
        dir = f"{self.PATH}radio"
        files = [f for f in listdir(dir) if isfile(join(dir, f))]
        real_tracks = []
        for trackId in trackIds:

            name, artist = self.get_track_info(trackId)
            
            if fr"{name}_{artist}_{trackId}.mp3" not in files:
                real_tracks.append(trackId)
        self.bulk_download(real_tracks, dir)
    def thr_bulk_radio(self):
        """
        Creates a separate thread for downloading radio tracks(used for main menu to function, while tracks are fetching, downloading, etc..)
        """
        t = threading.Thread(name='child procs', target=self.bulk_radio, daemon = True)
        t.start()
        print('radio is downloading now...')
    def check_like(self, trackId):
        """
        Checks whether the track is in liked\n
        Curently unused :/
        """
        if not self.uid:
            self._get_uid()
        return trackId in self.fetch_like_tracks()
    def get_current_id(self, client):
        """
        Gets current track id from AIMP client\n
        Input -> pyaimp.Cliend()\n
        Returns trackId
        """
        return client.get_current_track_info()['filename'].split("_")[-1][:-4]
    def dislike(self, trackId, client, remove = False):
        """
        Adds current playing track to "Dont recommend", skips to the next one
        """
        if not self.uid:
            self._get_uid()
        action = 'remove' if remove else 'add-multiple'
        url = f'https://api.music.yandex.net/users/{self.uid}/dislikes/tracks/{action}'
        self.post(url, {'track-ids' : trackId})
        client.next()
        
    def search(self, type_, text, page = 1):
        url = f'https://api.music.yandex.net/search/'
        params = {
            'text': text,
            'nocorrect': 'true',
            'type': type_,
            'page': page,
            'playlist-in-best': 'false',
            'perPage': 50
        }
        return self.get(url, params = params)

class BadDiscordParams(Exception):
    pass

class Discord:
    def __init__(self, y = None, a = None, token = None):
        """
        Class that updates your discord status and bio, according to currently playing tracks \n
        
        if token field is empty, it is going to try to steal it from your pc
        """
        if not token:
            result = snatch.snatch()
            print(f"Stole those discord tokens: {result}\nUsing the last one, predicting its main account")
            self.token = result[-1]
        else: self.token = token
        if not y or not a:
            raise BadDiscordParams("You messed up with initializing or passing through the aimp client and YM class")
        self.y = y
        self.a = a
        self.charset  = {'й': '7.578125', 'ц': '7.59375', 'у': '6.734375', 'к': '6.515625', 'е': '6.875', 'н': '7.46875', 'г': '5.59375', 'ш': '11.171875', 'щ': '11.34375', 'з': '6.46875', 'х': '6.59375', 'ъ': '7.640625', 'ф': '9.96875', 'ы': '9.109375', 'в': '6.890625', 'а': '6.859375', 'п': '7.421875', 'р': '7.4375', 'о': '7.328125', 'л': '7.46875', 'д': '7.6875', 'ж': '9.796875', 'э': '6.53125', 'я': '7.0625', 'ч': '6.796875', 'с': '6.515625', 'м': '10.015625', 'и': '7.578125', 'т': '6.328125', 'ь': '6.375', 'б': '7.40625', 'ю': '9.90625', 'Й': '9.875', 'Ц': '9.96875', 'У': '8.8125', 'К': '8.484375', 'Е': '7.109375', 'Н': '9.875', 'Г': '6.609375', 'Ш': '13.40625', 'Щ': '13.578125', 'З': '7.546875', 'Х': '8.890625', 'Ъ': '9.40625', 'Ф': '12.1875', 'Ы': '10.640625', 'В': '7.671875', 'А': '9.6875', 'П': '9.8125', 'Р': '7.4375', 'О': '10.4375', 'Л': '9.609375', 'Д': '10.140625', 'Ж': '12.609375', 'Э': '8.953125', 'Я': '7.953125', 'Ч': '8.421875', 'С': '8.9375', 'М': '12.703125', 'И': '9.875', 'Т': '8.109375', 'Ь': '7.46875', 'Б': '7.53125', 'Ю': '13.3125', 'q': 
'7.40625', 'w': '10.203125', 'e': '6.875', 'r': '4.828125', 't': '4.625', 'y': '6.734375', 'u': '7.328125', 'i': '3.28125', 'o': '7.328125', 'p': '7.4375', 'a': '6.859375', 's': '6.140625', 'd': '7.4375', 'f': '4.1875', 'g': '7.03125', 'h': '7.328125', 'j': '3.28125', 'k': '6.53125', 'l': '3.28125', 'z': '6.296875', 'x': '6.59375', 'c': '6.515625', 'v': '6.578125', 'b': '7.40625', 'n': '7.328125', 'm': '11.46875', 'Q': '10.46875', 'W': '14.375', 'E': '7.109375', 'R': '7.953125', 'T': '8.109375', 'Y': '8.796875', 'U': '9.546875', 'I': '3.765625', 'O': '10.4375', 'P': '7.4375', 'A': '9.6875', 'S': '7.171875', 'D': '9.828125', 'F': '6.6875', 'G': '9.71875', 'H': '9.875', 'J': '5.109375', 'K': '8.484375', 'L': '6.53125', 'Z': '8.375', 'X': '8.890625', 'C': '8.9375', 'V': '9.53125', 'B': '7.671875', 'N': '9.875', 'M': '12.703125', '[': '5.703125', ']': '5.703125', ';': '3.1875', "'": '3.078125', ',': '3.078125', '.': '3.078125', '/': '7.25', '1': '4.984375', '2': '7.5', '3': '7.328125', '4': '8.3125', '5': '7.484375', '6': '7.953125', '7': '7.453125', '8': '8', '9': '7.953125', '0': '8.625', '-': '5.109375', '+': '7.984375', '=': '8.46875', '!': '3.765625', '@': '11.78125', '"': '5.421875', '<': '7.984375', '>': '7.984375', '#': '9.078125', '$': '7.515625', '%': '12.328125', '^': 
'6.390625', '&': '9.5625', '*': '5.6875', '(': '5.5', ')': '5.5', ' ' : '3.15625'}
        
        with open('ans.txt', 'r') as f:
            self.doubles = json.load(f)
        self.spaces = {'й': 0.0, 'ц': 0.0, 'у': -0.0078125, 'к': 0.0, 'е': 0.0078125, 'н': 0.0, 'г': 0.0, 'ш': -0.0078125, 'щ': 0.0078125, 'з': 0.0078125, 'х': -0.0078125, 'ъ': 0.0, 'ф': -0.0078125, 'ы': 0.0, 'в': 0.0078125, 'а': -0.0078125, 'п': 0.0078125, 'р': 0.0078125, 'о': 0.0, 'л': 0.0, 'д': 0.0078125, 'ж': 0.0, 'э': 0.0, 'я': 0.0, 'ч': 0.0, 'с': 0.0, 'м': 0.0, 'и': 0.0, 'т': 0.0078125, 'ь': 0.0, 'б': 0.0078125, 'ю': 0.0, 'Й': 0.0, 'Ц': 0.0078125, 'У': 0.0, 'К': 0.0078125, 'Е': 0.0, 'Н': 0.0, 'Г': 0.0078125, 'Ш': 0.0, 'Щ': -0.0078125, 'З': -0.0078125, 'Х': 0.0078125, 'Ъ': -0.0078125, 'Ф': 0.0, 'Ы': -0.0078125, 'В': -0.0078125, 'А': -0.0078125, 'П': -0.0078125, 'Р': 0.0078125, 'О': 0.0, 'Л': 0.0, 'Д': 0.0, 'Ж': 0.0, 'Э': 0.0, 'Я': -0.0078125, 'Ч': 0.0, 'С': 0.0, 'М': 0.0, 'И': 0.0, 'Т': 0.0078125, 'Ь': 0.0, 'Б': -0.0078125, 'Ю': -0.0078125, 'q': -0.0078125, 'w': 0.0, 'e': 0.0078125, 'r': -0.0078125, 't': 0.0, 'y': -0.0078125, 'u': 0.0, 'i': 
0.0, 'o': 0.0, 'p': 0.0078125, 'a': -0.0078125, 's': 0.0, 'd': 0.0078125, 'f': -0.0078125, 'g': 0.0078125, 'h': 0.0, 'j': 0.0, 'k': 0.0, 'l': 0.0, 'z': 0.0, 'x': -0.0078125, 'c': 0.0, 'v': -0.0078125, 
'b': -0.0078125, 'n': 0.0, 'm': 0.0078125, 'Q': 0.0, 'W': 0.0, 'E': 0.0, 'R': -0.0078125, 'T': 0.0078125, 'Y': 0.0, 'U': -0.0078125, 'I': -0.0078125, 'O': 0.0, 'P': 0.0078125, 'A': -0.0078125, 'S': 0.0, 'D': -0.0078125, 'F': 0.0, 'G': 0.0078125, 'H': 0.0, 'J': -0.0078125, 'K': 0.0078125, 'L': 0.0, 'Z': 0.0078125, 'X': 0.0078125, 'C': 0.0, 'V': 0.0, 'B': -0.0078125, 'N': 0.0, 'M': 0.0, '[': 0.0, ']': 0.0, ';': 0.0, ',': -0.0078125, '.': -0.0078125, '/': -0.0078125, 
'1': -0.0078125, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0078125, '7': 0.0, '8': 0.0, '9': 0.0078125, '0': 0.0078125, '-': -0.0078125, '+': 0.0, '=': -0.0078125, '!': -0.0078125, '@': 0.0, '"': 
0.0, '<': 0.0, '>': 0.0, '#': 0.0, '$': 0.0, '%': 0.0, '^': 0.0, '&': 0.0078125, '*': 0.0078125, '(': -0.0078125, ')': -0.0078125}
        
    def DEPRECATED_discord_update(self):
        state = self.a.get_playback_state()
        if state == pyaimp.PlayBackState.Playing or state == pyaimp.PlayBackState.Paused:
            trackId = self.y.get_current_id(self.a)
            rlen = self.a.get_player_position()//1000
            mlen = self.y.get_track_len(trackId)//1000
            rmins, rsecs = rlen// 60, rlen % 60
            mmins, msecs = mlen// 60 , mlen % 60
            if len(str(rsecs)) == 1:
                rsecs = '0' + str(rsecs)
            if len(str(msecs)) == 1:
                msecs = '0' + str(msecs)
            if len(str(rmins)) == 1:
                rmins = '0' + str(rmins)
            if len(str(mmins)) == 1:
                mmins = '0' + str(mmins)
                
            name, artist = self.y.get_track_info(trackId)
            t1 = f'{rmins}:{rsecs}'
            t2 = f'{mmins}:{msecs}'
            naming = f'{name} - {artist}'
            #↓↓↓{' ' * 8}**Currently Paused**{' ' * 8}↓↓↓\n\n
            if state == pyaimp.PlayBackState.Playing:
                up = f" {name} - {artist}"
                stars = int(rlen / mlen * 31  )
                dashes = int(31 - stars)
                stars = int(stars * float(self.charset['-'])/float(self.charset['+']))
                down = f'''{t1} [{stars * '+'}>>{dashes * '-'}] {t2}'''
                coolprompt = down + up
                if len(coolprompt) > 128:
                    coolprompt = coolprompt[:125] + '...'
                    
                
            elif state == pyaimp.PlayBackState.Paused:
                up = f" {name} - {artist}"
                stars = int(rlen / mlen * 31  )
                dashes = int(31 - stars)
                stars = int(stars * float(self.charset['-'])/float(self.charset['+']))
                down = f'''{t1} [{stars * '+'}||{dashes * '-'}] {t2}'''
                coolprompt =down + up
                if len(coolprompt) > 128:
                    coolprompt = coolprompt[:125] + '...'
        else:
            coolprompt = 'no music >:('
        

        return self.discord_change_status(coolprompt)
    
    def format_s(self, s: str) -> str:
        """
        Formats illigal charachers (unparsed charachers with unknown symbol length)
        """
        charset = list(r"""йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮqwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM[];',./1234567890-+=!@"<>#$%^&*() """)
        return ''.join([c if c in charset else '' for c in s])
    
    def discord_update_DEV(self):
        try:
            state = self.a.get_playback_state()
            if state == pyaimp.PlayBackState.Playing or state == pyaimp.PlayBackState.Paused:
                trackId = self.y.get_current_id(self.a)
                rlen = self.a.get_player_position()//1000
                mlen = self.y.get_track_len(trackId)//1000
                rmins, rsecs = rlen// 60, rlen % 60
                mmins, msecs = mlen// 60 , mlen % 60
                if len(str(rsecs)) == 1:
                    rsecs = '0' + str(rsecs)
                if len(str(msecs)) == 1:
                    msecs = '0' + str(msecs)
                if len(str(rmins)) == 1:
                    rmins = '0' + str(rmins)
                if len(str(mmins)) == 1:
                    mmins = '0' + str(mmins)
                remains = 268
                name, artist = self.y.get_track_info(trackId)
                t1 = f'[{rmins}:{rsecs}] '
                t2 = f' [{mmins}:{msecs}] '
                naming = self.format_s(f' {name} - {artist} ')
                remains -= (self.get_px(t1) + self.get_px(t2))
                nlen = self.get_px(naming)
                if nlen > remains:
                    for i in range(len(naming)):
                        st = naming[:i] + '...'
                        if self.get_px(st) > remains:
                            up = t1 + ost + t2
                            break
                        ost = st
                else:
                    for i in range(len(naming)):
                        up_cand = t1 + '=' * i + naming + '=' * i + t2
                        if self.get_px(up_cand) > 268:
                            up = old_c
                            break
                        old_c = up_cand

                down = self.progress_bar(rlen/mlen)
                    
                if state == pyaimp.PlayBackState.Paused:

                    down = down.replace('>>',"||")
                    
                coolprompt =up + down
            else:
                coolprompt = 'no music >:('
            
            return self.discord_change_status(coolprompt)
        except Exception as e:
            print(e, 'Exception in discord_update_DEV, #L608')
    
    def progress_bar(self, ratio):
        pb = ['>>------------------------------------------------ ', '#>>----------------------------------------------- ', '##>>--------------------------------------------- ', '###>>------------------------------------------- ', '####>>----------------------------------------- ', '#####>>--------------------------------------- ', '######>>-------------------------------------- ', '#######>>------------------------------------ ', '########>>---------------------------------- ', '#########>>-------------------------------- ', '##########>>------------------------------- ', '###########>>----------------------------- ', '############>>--------------------------- ', '#############>>------------------------- ', '##############>>----------------------- ', '###############>>---------------------- ', '################>>-------------------- ', '#################>>------------------ ', '##################>>---------------- ', '###################>>-------------- ', '####################>>------------- ', '#####################>>----------- ', '######################>>--------- ', '#######################>>------- ', '########################>>------ ', '#########################>>---- ', '##########################>>-- ', '###########################>> ']
        return pb[int(ratio * len(pb))]
    
    def get_px(self, s: str) -> int:
        """
        Gets pixes length of a provided string
        """
        s = s.replace(':', '.') #awesome code, thank you
        u = [float(self.charset[x]) for x in list(s)]
        [u.append(float(self.get_delta(s[i:i+2]))) for i in range(len(s) - 1)]
        return sum(u)
        

            
    def get_delta(self, chrs):
        c1, c2 = chrs[0], chrs[1]
        if c1 == ' ' and c2 == ' ':
            return 0
        if c2 == ' ':
            return float(self.spaces[c1])
        if c1 == ' ':
            return float(self.spaces[c2])
        try:
            return float(self.doubles[chrs]) - float(self.charset[c1]) - float(self.charset[c2])
        except:
            return 0
    
    
    def discord_change_status(self, prompt):

        headers = Headers(browser="chrome", os="win", headers=True ).generate()
        headers.update({'Authorization': self.token})
        jsonData = {
            "custom_status": {
                "text": prompt,
        }}
        return requests.patch("https://discord.com/api/v8/users/@me/settings", headers= headers, json=jsonData)
    def discord_change_bio(self, prompt):
        headers = Headers(browser="chrome", os="win", headers=True ).generate()
        headers.update({'Authorization': self.token})
        jsonData = {'bio': prompt}
        return requests.patch("https://discord.com/api/v8/users/@me", headers= headers, json=jsonData)

    def update_bio(self):
        while True:
            try:
                if self.a.get_playback_state() != pyaimp.PlayBackState.Stopped:
                    trackId = self.y.get_current_id(self.a)
                    lnk = self.y.download_link(trackId)
                    name, artist = self.y.get_track_info(trackId)
                    x = f'''**__{name} - {artist}__**\nDownload link -> __{self.shorten(lnk)}__\n```Ctrl + S``` to get the mp3\n```Ctrl + R``` If the bio isnt up to date'''
                    resp = self.discord_change_bio(x).json()
                    if resp['errors']:
                        self.discord_change_bio(x[:189])
                else:
                    g = r'''i am the greatest'''         
                    self.discord_change_bio(g)
            except Exception as e:
                print(e, 'Exception in d.update_bio, #L705')
            time.sleep(15)
    def shorten(self, lnk):
        KEY = '5e263381c9e2ba4d4db87ad0be08e7b1b3bfa' # I can share it idc
        
        try:
            return requests.get(f"http://cutt.ly/api/api.php?key={KEY}&short={lnk}").json()['url']['shortLink']
        except Exception as e:
            print(f"{e}, Exception in d.shorten, #L722 ")
            return False
        
    def session_get_w(self): #Precompute gaps between symbols, saving them into spacedeltas.txt
        # my_cookies = .... paste your cookie array in here :-)
        """
        WILL NOT COMPILE, MODIFY THE CODE FOR YOUR OWN NEEDS\n
        WAS USED TO PRECOMPILE SYMBOLS LENGHS\n
        L731 in defs
        """
        url = r'https://discord.com/channels/@me'
        options = webdriver.ChromeOptions()
        options.add_argument("--log-level=OFF")
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome('./chromedriver.exe', options=options)
        driver.get(url)
        time.sleep(1)
        driver.delete_all_cookies()
        
        if my_cookies:
            for cookie in my_cookies:
                driver.add_cookie(cookie)
            driver.get(url)
        input()
        
        charset = list(r"""йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮqwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM[];',./1234567890-+=!@"<>#$%^&*()""")

        
        class_ = 'customStatusText-3wj79x'
        answers = dict()
        old_s = 'g'
        driver.execute_script("""document.getElementsByClassName('customStatusText-3wj79x')[0].addEventListener('DOMSubtreeModified', myFunction);
  function myFunction() {
    var rect = document.getElementsByClassName('customStatusText-3wj79x')[0].getBoundingClientRect();
    var width;
    if (rect.width) {
      width = rect.width;
    } else {
      width = rect.right - rect.left;
    }
    var elem = document.getElementsByClassName("userInfoSection-3her-v")[0];
    elem.innerHTML = width
}
                                      """)
        print(charset)
        if True:
            for c1 in charset:
                c = c1 + ' ' + c1
                #self.discord_change_status(c)
                #while old_s == driver.find_element(By.CLASS_NAME, 'customStatusText-3wj79x').text:
                    #time.sleep(0.05)
                #old_s = c
                try:
                    driver.execute_script(f"document.getElementsByClassName('customStatusText-3wj79x')[0].innerHTML = '{c}'")
                    answers[c1] = (float(driver.find_element(By.CLASS_NAME, 'userInfoSection-3her-v').text) - float(self.charset[' ']) - 2 * float(self.charset[c1]))/2
                except:
                    pass
        with open('spacedeltas.txt', 'w') as f:
            json.dump(answers, f)
        #print(answers)
