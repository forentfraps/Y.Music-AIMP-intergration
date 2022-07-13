# Y.Music-AIMP-intergration


## External addon for AIMP to work with Yandex Music


### Setting things up
  - run ```pip install -r requirements.txt``` in directory with this repo
  - Open your browser and type in the link: ```https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d```
  - Authorize
  - That is it, my script will steal cookies from your browser (only yandex.ru domain), hence keep your browser up, when launching 1st time


### Usage
The first lauch may take a while (to set up folders), however, all the next ones will be quite quick

Script is written to work in synergy with AIMP, thus you require it. (I was using 3.x.x version, should work fine with any other version)

Most of the inspiration and api requests were taken from https://github.com/MarshalX/yandex-music-api (huge thanks)

Code is well commented and documented



Thats how the main menu looks (Great design choices, thank you)

![image](https://user-images.githubusercontent.com/29946764/178856802-10821809-54ed-4ff3-90dd-bc11ec657b6f.png)
