import requests

def test0():
    # url="https://sns-video-bd.xhscdn.com/1040g00g30rqhqh18iq005p1505n4idj9473h21g"
    url="https://sns-video-bd.xhscdn.com/1040g2so30slnstpvka6g49932qu30e21h2rgagg"
    if url.startswith("http:"):
        url=f'https:{url[5:]}'
    resp = requests.head(url)
    print(resp.status_code)
    print(resp.headers.get("Content-Length"))
    print(resp.headers.get("Content-Type"))
    print(len(resp.content))
    resp.close()


if __name__ == '__main__':
    test0()