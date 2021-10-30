from traceback import format_exc
import requests
import time
import datetime
import json
import random
import threading
import os

lock = threading.Lock()


def scrap(keyword):
    keyword_list: list = requests.get("http://127.0.0.1:8000/all-keywords").json()["keyword_list"]
    id_counter = keyword_list.index(keyword) // 30
    base_url = "https://graph.facebook.com/v12.0/"
    params = dict()
    with open("./graph_api_secret.json", 'r', encoding="UTF8") as f:
        account_info = json.load(f)
    account = account_info["accounts"][id_counter]
    params["user_id"] = account["user_id"]
    params["access_token"] = account["access_token"]
    params["fields"] = "permalink,caption"
    params["limit"] = "9"
    with open("./hashtag_id.json", 'r', encoding="UTF8") as f:
        hashtag_id = json.load(f)[keyword]
    url = base_url + hashtag_id + "/top_media"
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

    if len(posts) == 0:
        keyword_list = requests.get("http://127.0.0.1:8000/keywords").json()["keyword_list"]
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
        res = requests.post("http://127.0.0.1:8000/posts", headers=headers, data=payload)
        print(res.status_code)
        return 0

    print(datetime.datetime.now())
    for post in reversed(posts):
        post_id = post["permalink"][-12:-1]
        post_url = post["permalink"][:-12].replace("tv", 'p') + post_id + '/'
        print(post_url)
        img_url = post_url + "media/?size=l"
        print(img_url)
        print(keyword)
        if requests.get(
                "http://127.0.0.1:8000/post/" + keyword + '/' + post_id).status_code == 200:
            continue

        headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"
        }
        lock.acquire()
        time.sleep(1)
        res = requests.get(img_url, headers=headers)
        lock.release()

        if "image" not in res.headers["content-type"]:
            with open("image_open_error" + str(datetime.datetime.now()).replace(':', '.') + ".txt", 'w', encoding="UTF8") as f:
                f.write(post_url + '\n' + img_url + '\n' + keyword)
            os._exit(0)

        if not os.path.exists("F:/nginx/html/" + keyword):
            os.makedirs("F:/nginx/html/" + keyword)

        with open("F:/nginx/html/" + keyword + '/' + post_id + ".jpg", "wb") as f:
            f.write(res.content)


        files=[('images', (post_id + '.jpg', open('F:/nginx/html/' + keyword + '/' + post_id + '.jpg','rb'), 'image/jpeg'))]
        res = requests.post("http://127.0.0.1:5000/detections/by-image-files", files=files)
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
                "insta_analysis": insta_analysis,
                "insta_analysis_food": insta_analysis_food,
                "is_ad": is_ad
            }
        )
        res = requests.post("http://127.0.0.1:8000/posts", headers=headers, data=payload)
        print(res.status_code)
        if res.status_code == 400:
            print(payload)
    print("id_counter: " + str(id_counter))
    print(app_usage)
    return app_usage["total_time"]


def validate_keyword(keyword):
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
    keyword_list = requests.get("http://127.0.0.1:8000/all-keywords").json()["keyword_list"]
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
    while True:
        keyword_list = requests.get("http://127.0.0.1:8000/not-scraped-yet").json()["keyword_list"]
        for keyword in keyword_list:
            if validate_keyword(keyword):
                scrap(keyword)
                time.sleep(36)
            else:
                res = requests.delete("http://127.0.0.1:8000/post/" + keyword + "/dummy")
                print(res.status_code)
        time.sleep(3)


def slow_scrap_thread(keyword_list: list):
    sleep_time = 600
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
    rounds = 0
    while True:
        keyword_list = requests.get("http://127.0.0.1:8000/keywords").json()["keyword_list"]
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
