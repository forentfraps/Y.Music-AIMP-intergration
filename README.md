# Y.Music-AIMP-intergration


##External addon for AIMP to work with Yandex Music


### Logging in (aka getting the token)
  - Open your browser and type in the link : ```https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d```
  - Authorise
  - That is it, my script will steal cookies from your browser (only yandex.ru domain), hence keep your browser up, when launching 1st time


### Usage
The first lauch may take a while (to set up folders), however, all the next ones will be quite quick

The interface is in russian, because the tool was designed for russian music service, although if you check the code, it becomes quite trivial what is what

Script is written to work in synergy with AIMP, thus you require it. (I was using 3.x.x version, should work fine with any other version)

I will document the code in a while, although most of the inspiration and api requests were taken from https://github.com/MarshalX/yandex-music-api (huge thanks)
