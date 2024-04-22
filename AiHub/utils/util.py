from http.cookies import SimpleCookie

def parse_cookie_string(cookie_str):
    cookie_map = {}
    cookie = SimpleCookie()
    cookie.load(cookie_str)

    for key, morsel in cookie.items():
        cookie_map[key] = morsel.value

    return cookie_map