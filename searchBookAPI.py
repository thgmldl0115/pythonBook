import requests

def get_naver(query):
    url = f"https://openapi.naver.com/v1/search/book.json?query={query}"
    CLIENT_ID = "GQnxFMtjYg6wNjZ0T7B5"
    SECRET = "bBN3EbdKnM"
    header = {"X-Naver-Client-Id": CLIENT_ID
              ,"X-Naver-Client-Secret":SECRET}
    res = requests.get(url, headers=header)
    json_data = res.json()
    items = json_data['items']
    books_data = []
    for item in items:

        book_data = {'title':item['title']
                    ,'image':item['image']
                    ,'author':item['author']
                    ,'discount':item['discount']
                    ,'isbn':item['isbn']}

        books_data.append(book_data)
    return books_data

# books = get_naver('김초엽')
# print(len(books))
# for book in books:
#     print(book)
