import requests

def get_detail(isbn):
    url = f"https://www.nl.go.kr/seoji/SearchApi.do?cert_key=[cccb0fb8ce564c16a51cbc69e98cf545c661fd9c4c426ab2e3578ac7dd6ec0e3]&result_style=json&page_no=1&page_size=2&isbn={isbn}"
    res = requests.get(url)
    json_data = res.json()

    return json_data

arr = get_detail('9791160406504')
print(arr)