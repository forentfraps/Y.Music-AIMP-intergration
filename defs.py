import datetime
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


class YM:
    def __init__(self, debug = False):
        self.s = requests.Session()
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
        if not exists('./Y'):
            mkdir('./Y')
        if not exists('./Y/daily'):
            mkdir('./Y/daily')
        if not exists('./Y/likes'):
            mkdir('./Y/likes')
        if not exists('./Y/radio'):
            mkdir('./Y/radio')
        if not exists('./Y/daily_ups.txt'):
            with open('./Y/daily_ups.txt','w') as f:
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
        if exists("./Y/token.txt"):
            with open("./Y/token.txt", 'r') as f:
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
        with open('./Y/token.txt', "w") as f:
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
        remove: bool == If true will remove the like instead
        """
        if not self.uid:
            self._get_uid()
        action = 'remove' if remove else 'add-multiple'
        link = f'https://api.music.yandex.net/users/{self.uid}/likes/tracks/{action}'
        self.post(link, {"track-ids": trackId})
        if not remove:
            self.download(trackId, "./Y/likes")
        
        
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
        dir = "./Y/daily"
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
        t = threading.Thread(name='child procs', target=self.bulk_download_daily)
        t.start()
    def bulk_download_like(self):
        """
        Downloads liked tracks
        """
        tracks =  self.fetch_like_tracks()
        dir = "./Y/likes"
        
        files = [f for f in listdir(dir) if isfile(join(dir, f))]
        trackIds = list(filter(bool, [trackId if trackId not in tracks else 0 for trackId in list(map(lambda x: x.split("_")[-1][:-4], files))]))
        self.bulk_download(trackIds, dir)
        
        print("done")
    def thr_bulk_download_like(self):
        """
        Creates a separate thread for downloading liked (used for main menu to function, while tracks are fetching, downloading, etc..)
        """
        t = threading.Thread(name='child procs', target=self.bulk_download_like)
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
        dir = "./Y/radio"
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
        t = threading.Thread(name='child procs', target=self.bulk_radio)
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
