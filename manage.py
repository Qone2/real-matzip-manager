from traceback import format_exc
import requests
import time
import datetime
import json
import random
import threading
import os

from ip_change import ip_change

lock = threading.Lock()


def scrap(keyword):
    """
    메인 스크랩 함수.
    키워드(해시태그)를 받아 스크랩작업을 한다.
    """
    # 몇번째로 등록된 키워드인지 파악하여 몇번째 계정으로 instagram graph api 에 접속할 것인지 파악
    keyword_list: list = requests.get("http://127.0.0.1:8443/all-keywords").json()["keyword_list"]
    id_counter = keyword_list.index(keyword) // 30

    # instagram graph api 쿼리
    base_url = "https://graph.facebook.com/v12.0/"
    params = dict()
    with open("./graph_api_secret.json", 'r', encoding="UTF8") as f:
        account_info = json.load(f)
    account = account_info["accounts"][id_counter]
    params["user_id"] = account["user_id"]
    params["access_token"] = account["access_token"]
    params["fields"] = "permalink,caption,timestamp"
    params["limit"] = "50"
    # 해시태그 고유 id 필요
    with open("./hashtag_id.json", 'r', encoding="UTF8") as f:
        hashtag_id = json.load(f)[keyword]
    url = base_url + hashtag_id + "/recent_media"
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"
    }
    res = requests.get(url, params, headers=headers)
    if res.status_code != 200:
        with open("scrap_insta_server_error" + str(datetime.datetime.now()).replace(':', '.') + ".html", 'w', encoding="UTF8") as f:
            f.write(res.text)
        os._exit(0)
    posts = res.json()["data"]
    app_usage: dict = json.loads(res.headers["x-app-usage"])

    # 해시태그는 있으나 정작 내용은 없는 경우, 더미 게시글을 하나 더 포스트해서 스크랩되지 않은 목록에서 제외한다.
    # 스크랩되지 않은 키워드 목록은 게시글 수가 1개만 있는 경우에 해당한다.
    if len(posts) == 0:
        keyword_list = requests.get("http://127.0.0.1:8443/keywords").json()["keyword_list"]
        if keyword in keyword_list:
            return 0
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps(
            {
                "post_id": "dummy1",
                "post_url": "dummy1",
                "img_url": "https://images.unsplash.com/photo-1604147706283-d7119b5b822c",
                "keyword": keyword,
                "post_text": "dummy1",
                "insta_analysis": "dummy1",
                "insta_analysis_food": False,
                "is_ad": False
            }
        )
        res = requests.post("http://127.0.0.1:8443/posts", headers=headers, data=payload)
        print(res.status_code)
        return 0

    # 스크랩 과정
    print(datetime.datetime.now())
    for post in reversed(posts):
        post_id = post["permalink"][-12:-1]
        post_url = post["permalink"][:-12].replace("tv", 'p') + post_id + '/'
        posted_date = post["timestamp"]
        print(post_url)
        img_url = post_url + "media/?size=l"
        print(img_url)
        print(keyword)

        # 이미 있는 포스트면 제외
        if requests.get(
                "http://127.0.0.1:8443/post/" + keyword + '/' + post_id).status_code == 200:
            continue

        headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"
        }

        # 인스타그램 포스트 미디어주소를 통해 사진을 다운받는 과정. 스레드마다 텀을 두어 요청한다.
        lock.acquire()
        time.sleep(1 + random.uniform(-0.5, 0.5))
        try:
            res = requests.get(img_url, headers=headers)
        except Exception as e:
            with open("page_request_error" + str(datetime.datetime.now()).replace(':', '.') + ".txt", 'w', encoding="UTF8") as f:
                f.write(post_url + '\n' + img_url + '\n' + keyword + '\n' + str(e.__class__) + '\n' + str(e))
            lock.release()
            continue

        # ip 변경
        if "image" not in res.headers["content-type"]:
            with open("image_open_error" + str(datetime.datetime.now()).replace(':', '.') + ".txt", 'w', encoding="UTF8") as f:
                f.write(post_url + '\n' + img_url + '\n' + keyword)
            ip_change()
            print(">>>> ip changed")
            lock.release()
            continue
        lock.release()

        # 사진파일 저장 nginx 나 apache 또는 static 폴더에 저장
        if not os.path.exists("F:/nginx/html/" + keyword):
            os.makedirs("F:/nginx/html/" + keyword)
        with open("F:/nginx/html/" + keyword + '/' + post_id + ".jpg", "wb") as f:
            f.write(res.content)

        # Object detection 서버에 detection 요청
        files = [('images', (post_id + '.jpg', open('F:/nginx/html/' + keyword + '/' + post_id + '.jpg','rb'), 'image/jpeg'))]
        res = requests.post("http://127.0.0.1:5050/detections/by-image-files", files=files)
        if res.status_code != 200:
            with open("object_detection_error" + str(datetime.datetime.now()).replace(':', '.') + ".txt", 'w', encoding="UTF8") as f:
                f.write(post_url + '\n' + img_url + '\n' + keyword)
            os._exit(0)
        food_score = 0.0
        for detection in res.json()["response"][0]["detections"]:
            if detection["confidence"] > food_score:
                food_score = detection["confidence"]
        post_text = ""
        try:
            post_text = post["caption"]
        except KeyError:
            pass
        insta_analysis = ""
        insta_analysis_food = False
        is_ad = False
        if "광고" in post_text or "협찬" in post_text:
            is_ad = True
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps(
            {
                "post_id": post_id,
                "post_url": post_url,
                "img_url": img_url,
                "keyword": keyword,
                "food_score": food_score,
                "post_text": post_text,
                "posted_date": posted_date,
                "insta_analysis": insta_analysis,
                "insta_analysis_food": insta_analysis_food,
                "is_ad": is_ad
            }
        )
        # 메인 api 서버에 포스트 저장
        res = requests.post("http://127.0.0.1:8443/posts", headers=headers, data=payload)
        print(res.status_code)
        if res.status_code == 400:
            print(payload)
    print("id_counter: " + str(id_counter))
    print(app_usage)
    return app_usage["total_time"]


def validate_keyword(keyword):
    """
    키워드(string)가 유효한지 파악하여 true false 리턴
    '유효' 하다는 뜻은 우선 키워드에 '맛집' 이라는 단어가 포함되어 있어야 하고,
    instagram graph api 에서 해시태그 id가 존재하는 키워드 이어야 한다.
    """
    if "맛집" not in keyword:
        return False
    with open("./hashtag_id.json", "r", encoding="UTF8") as f:
        hashtag_dict: dict = json.load(f)
    if hashtag_dict.get(keyword) is not None:
        return True
    url = "https://graph.facebook.com/v12.0/ig_hashtag_search"
    params = dict()
    with open("./graph_api_secret.json", 'r', encoding="UTF8") as f:
        account_info = json.load(f)
    keyword_list = requests.get("http://127.0.0.1:8443/all-keywords").json()["keyword_list"]
    id_counter = keyword_list.index(keyword) // 30
    account = account_info["accounts"][id_counter]
    params["user_id"] = account["user_id"]
    params["access_token"] = account["access_token"]
    params["q"] = keyword
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"
    }
    res = requests.get(url, params, headers=headers)

    if res.status_code == 400:
        return False
    elif res.status_code != 200:
        with open("validate_keyword_server_error" + str(datetime.datetime.now()).replace(':', '.') + ".html", 'w', encoding="UTF8") as f:
            f.write(res.text)
        os._exit(0)

    hashtag_id = res.json()["data"][0]["id"]
    lock.acquire()
    with open("./hashtag_id.json", "r", encoding="UTF8") as f:
        hashtag_dict = json.load(f)
    hashtag_dict[keyword] = hashtag_id
    with open("./hashtag_id.json", "w", encoding="UTF8") as f:
        json.dump(hashtag_dict, f, indent=2, ensure_ascii=False)
    lock.release()
    time.sleep(36)
    return True


def fast_scrap():
    """
    더 빠른 스크랩을 위한 함수.
    아직 스크랩되지 않은 키워드를 주기적으로 메인 api 서버로 쿼리하고,
    존재한다면 스크랩을 진행한다.
    """
    while True:
        try:
            keyword_list = requests.get("http://127.0.0.1:8443/not-scraped-yet").json()["keyword_list"]
        except:
            time.sleep(3)
            continue
        for keyword in keyword_list:
            if validate_keyword(keyword):
                scrap(keyword)
                time.sleep(36)
            else:
                res = requests.delete("http://127.0.0.1:8443/post/" + keyword + "/dummy")
                print(res.status_code)
        time.sleep(3)


def slow_scrap_thread(keyword_list: list):
    """
    느린 스크랩을 하기 위한 하나의 쓰레드 함수.
    쪼개진 키워드 리스트를 받아 스크랩 함수를 실행한다.
    """
    sleep_time = 75  # 75 ~ 2400
    prev_usage = 0
    for keyword in keyword_list:
        if validate_keyword(keyword):
            usage = scrap(keyword)
            if prev_usage == 0 and usage == 0:
                sleep_time -= 1
            elif prev_usage - usage > 0:
                sleep_time -= 1
            elif prev_usage - usage == 0:
                pass
            elif prev_usage - usage < 0:
                sleep_time += 1
            prev_usage = usage
            print("sleep " + str(sleep_time) + "secs")
            time.sleep(sleep_time)


def slow_scrap():
    """
    느린 스크랩을 위한 함수.
    메인 api 서버로부터 해시태그 목록을 받아 30개 단위로 나눈 후,
    (30개 단위로 나누는 이유는 각 instagram graph api 계정마다 쿼리할 수 있는 해시태그 종류가 최대 30개 이기떄문)
    느린 속도로 스크랩을 진행한다.
    """
    rounds = 0
    while True:
        keyword_list = requests.get("http://127.0.0.1:8443/keywords").json()["keyword_list"]
        keyword_lists = list()
        threads = list()
        for i in range(len(keyword_list) // 30 + 1):
            keyword_lists.append(keyword_list[i * 30:i * 30 + 30])
        for keyword_list in keyword_lists:
            thread = threading.Thread(target=slow_scrap_thread, args=(keyword_list, ))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        print("rounds: " + str(rounds))
        time.sleep(3)
        rounds += 1


def main():
    thread0 = threading.Thread(target=fast_scrap, name="thread0")
    thread0.start()
    thread1 = threading.Thread(target=slow_scrap, name="thread1")
    thread1.start()


if __name__ == "__main__":
    main()
