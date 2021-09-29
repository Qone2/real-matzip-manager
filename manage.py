from traceback import format_exc
import requests
import time
import datetime
import json
import random
import threading


def crawl(keyword):
    keyword_list: list = requests.get("http://127.0.0.1:8000/all-keywords").json()["keyword_list"]
    id_counter = keyword_list.index(keyword) // 30
    base_url = "https://graph.facebook.com/v12.0/"
    params = dict()
    with open("./graph_api_secret.json", 'r') as f:
        account_info = json.load(f)
    account = account_info["accounts"][id_counter]
    params["user_id"] = account["user_id"]
    params["access_token"] = account["access_token"]
    params["fields"] = "permalink,caption"
    with open("./hashtag_id.json", 'r') as f:
        hashtag_id = json.load(f)[keyword]
    url = base_url + hashtag_id + "/top_media"
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"
    }
    res = requests.get(url, params, headers=headers)
    if res.status_code != 200:
        with open("crawl_insta_server_error" + str(datetime.datetime.now()) + ".html", 'w') as f:
            f.write(res.text)
        raise
    posts = res.json()["data"]

    if len(posts) == 0:
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
        return

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
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "images": [
                img_url
            ]
        })
        res = requests.post("http://127.0.0.1:5000/detections/by-url-list", headers=headers, data=payload)
        if res.status_code != 200:
            with open("object_detection_error" + str(datetime.datetime.now()) + ".txt", 'w') as f:
                f.write(post_url + '\n' + img_url + '\n' + keyword)
            continue
        food_score = 0.0
        for detection in res.json()["response"][0]["detections"]:
            if detection["confidence"] > food_score:
                food_score = detection["confidence"]
        post_text = post["caption"]
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


def validate_keyword(keyword):
    if "맛집" not in keyword:
        return False
    with open("./hashtag_id.json", "r") as f:
        hashtag_dict: dict = json.load(f)
    if hashtag_dict.get(keyword) is not None:
        return True
    url = "https://graph.facebook.com/v12.0/ig_hashtag_search"
    params = dict()
    with open("./graph_api_secret.json", 'r') as f:
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
        with open("validate_keyword_server_error" + str(datetime.datetime.now()) + ".html", 'w') as f:
            f.write(res.text)
        raise

    hashtag_id = res.json()["data"][0]["id"]
    with open("./hashtag_id.json", "r") as f:
        hashtag_dict = json.load(f)
    hashtag_dict[keyword] = hashtag_id
    with open("./hashtag_id.json", "w") as f:
        json.dump(hashtag_dict, f, indent=2, ensure_ascii=False)

    return True


def fast_crawl():
    while True:
        keyword_list = requests.get("http://127.0.0.1:8000/not-crawled-yet").json()["keyword_list"]
        for keyword in keyword_list:
            if validate_keyword(keyword):
                crawl(keyword)
                time.sleep(2)
            else:
                res = requests.delete("http://127.0.0.1:8000/post/" + keyword + "/dummy")
                print(res.status_code)
        time.sleep(2)


def slow_crawl():
    while True:
        keyword_list = requests.get("http://127.0.0.1:8000/keywords").json()["keyword_list"]
        for keyword in keyword_list:
            if validate_keyword(keyword):
                crawl(keyword)
                time.sleep(18)
        time.sleep(18)


def main():
    threading.Thread(target=fast_crawl).start()
    threading.Thread(target=slow_crawl).start()


if __name__ == "__main__":
    main()
