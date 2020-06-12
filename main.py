import requests
from pathlib import Path
from bs4 import BeautifulSoup
import os
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
import json
import argparse


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


def parse_book_information(url):
    response = requests.get(url)
    response.raise_for_status()
    if not response.history:
        response_soup = BeautifulSoup(response.text, 'lxml')

        header_element_text = response_soup.select_one('.ow_px_td h1').get_text()
        book_header = header_element_text.split('\xa0')[0].strip()
        book_author = header_element_text.split('\xa0')[2].strip()

        image_source = response_soup.select_one('.bookimage img')['src']
        image_link = urljoin('http://tululu.org/', image_source)

        comments = [comment.text for comment in response_soup.select('.texts .black')]

        genres = [genre.text for genre in response_soup.select('span.d_book > a')]

        book_information = {'title': book_header,
                            'author': book_author,
                            'comments': comments,
                            'image_src': image_link,
                            'genres': genres
                            }
        return book_information


def get_books_links(start, end):
    science_fiction_books_links = []

    for page_number in range(start, end+1):
        url = 'http://tululu.org/l55/{}/'.format(page_number)
        response = requests.get(url)
        response_soup = BeautifulSoup(response.text, 'lxml')

        book_cards = response_soup.select('#content .d_book')

        for book in book_cards:
            book_link = urljoin('http://tululu.org/', book.select_one('a')['href'])
            book_id = (book.select_one('a')['href'])[2:-1]
            science_fiction_books_links.append((book_link, book_id))

    return science_fiction_books_links

def parse_console_arguments():
    parser = argparse.ArgumentParser(description='Парсинг книг из онлайн библиотеки.')
    parser.add_argument('-s', '--start_page', help = 'Начальная страница', default=1, type=int)
    parser.add_argument('-e', '--end_page', help = 'Конечная страница', default=1, type=int)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_console_arguments()

    science_fiction_books_links = get_books_links(args.start_page, args.end_page)
    books_information = []

    for link, id in science_fiction_books_links:
            book_information = parse_book_information(link)

            txt_url = 'http://tululu.org/txt.php?id={}'.format(id)
            book_name = '{}. {}'.format(id, book_information['title'])
            book_information['book_path'] = download_txt(txt_url, book_name, folder='books/')

            image_filename = (book_information['image_src']).split('/')[-1]
            book_information['image_src'] = download_image(book_information['image_src'], image_filename)

            books_information.append(book_information)

    with open('books_information.json', 'w', encoding='utf-8') as file:
        json.dump(books_information, file, ensure_ascii=False, indent=2)

