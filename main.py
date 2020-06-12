import requests
from pathlib import Path
from bs4 import BeautifulSoup
import os
from pathvalidate import sanitize_filename
from urllib.parse import urljoin


def download_txt(url, filename, folder='books/'):
    Path(folder).mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    if not response.history:
        filename = sanitize_filename(filename) + '.txt'
        filepath = os.path.join(folder, filename)
        with open(filepath, 'w') as file:
            file.write(response.text)
        return filepath

def download_image(url, filename, folder='images/'):
    Path(folder).mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    if not response.history:
        filename = sanitize_filename(filename)
        filepath = os.path.join(folder, filename)
        with open(filepath, 'wb') as file:
            file.write(response.content)
        return filepath

def fetch_book_page(id):
    url = 'http://tululu.org/b{}'.format(id)
    response = requests.get(url)
    response.raise_for_status()
    if len(response.history) == 1:
        response_soup = BeautifulSoup(response.text, 'lxml')
        header_element_text = response_soup.find('td', class_='ow_px_td').find('h1').text
        book_header = header_element_text.split('\xa0')[0].strip()
        image_source = response_soup.find('div', class_='bookimage').find('img')['src']
        image_link = urljoin('http://tululu.org/', image_source)
        return book_header, image_link


if __name__ == '__main__':

    for id in range(1, 11):
        try:
            url = 'http://tululu.org/txt.php?id={}'.format(id)
            book_header, image_link = fetch_book_page(id)
            filename = image_link.split('/')[-1]
            download_image(image_link, filename)
            book_name = '{}. {}'.format(id, book_header)
            download_txt(url, book_name, folder='books/')
        except TypeError:
            continue
