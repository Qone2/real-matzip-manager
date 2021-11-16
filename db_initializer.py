import json
import requests

with open("./hashtag_id.json", "r", encoding="UTF8") as f:
        hashtag_dict = json.load(f)

for hashtag in hashtag_dict:
    print(hashtag)
    res = requests.post("http://127.0.0.1:8443/post/" + hashtag)
    print(res.status_code)

    headers = {
            'Content-Type': 'application/json'
    }
    payload = json.dumps(
        {
            "post_id": "dummy1",
            "post_url": "dummy1",
            "img_url": "https://images.unsplash.com/photo-1604147706283-d7119b5b822c",
            "keyword": hashtag,
            "post_text": "dummy1",
            "insta_analysis": "dummy1",
            "insta_analysis_food": False,
            "is_ad": False
        }
    )
    res = requests.post("http://127.0.0.1:8443/posts", headers=headers, data=payload)
    print(res.status_code)