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


## Discord addon
Now has a discord addon(aka selfbotting), which works very spotify alike.

It shows in your status dynamically changing progress bar of your song and its name

In the bio it provides a direct link to it. The status updates every 0.5 seconds on your side and about once per 3 seconds on everyone elses client.

The bio updates once per 30 seconds.

![image](https://user-images.githubusercontent.com/29946764/189736916-95c81598-6c22-4fbb-bd96-2b74d51e0e81.png)
![image](https://user-images.githubusercontent.com/29946764/189736936-8b67f484-af34-486b-a474-06a1db70181c.png)

### Note
Dont forget to add a token in main.pyw, otherwise it will steal it from your computer and use what its found

It could be from an another account, so please pass the token, when initializing Discord() class
