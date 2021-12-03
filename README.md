# Real Matzip API
진짜맛집 프로젝트의 메니지먼트 서버.
https://github.com/Qone2/real-matzip-api, https://github.com/Qone2/YOLOv4-Object-Detection-API-Server 두 서버와 연계되어 작동하며
인스타그램 공식 api를 통해 해시태그 에 대한 포스트들을 검색하고 포스트내용을 스크랩하며, 포스트마다 고유한 미디어 주소를 통해 사진을 스크랩하여 저장합니다.

## Install
### pip
```shell
pip install -r requirements.txt
```

### Initiate
```shell
python db_initializer.py
```

### For ip_change.py
프로젝트 폴더에 크롬드라이버가 있어야 합니다.<br>
ASUS 라우터를 대상으로 설정되어있습니다. <br>
사진파일을 다운받기 위해서는 "https://www.instagram.com/p/CVRII8mh4WR/media/?size=l" 같이 미디어 주소로 부터 사진을 가져와야 합니다. <br>
그런데 접속 횟수가 늘어나면, 따로 로그인을 요구하게 되고 이후에 벤이 이루어 지므로 public ip를 지속적으로 바꾸기 위한 장치 입니다.

### Needed server
https://github.com/Qone2/real-matzip-api <br>
https://github.com/Qone2/YOLOv4-Object-Detection-API-Server <br>
두 서버가 미리 활성화 되어있어야 합니다.

### Settings for .json
hashtag_id.json, graph_api_secret.json 두 파일이 미리 설정되어 있어야 합니다.

### Run
```shell
python manage.py
```
