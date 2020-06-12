import requests
from pathlib import Path


def download_book(url, filename):
    Path("./books").mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    if not response.history:
        with open(filename, 'w') as file:
            file.write(response.text)


if __name__ == '__main__':
    for id in range(1,10):
        url = 'http://tululu.org/txt.php?id={}'.format(id)
        filename = './books/id' + str(id)
        download_book(url, filename)

