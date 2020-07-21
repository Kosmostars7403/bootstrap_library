import requests
from pathlib import Path
from bs4 import BeautifulSoup
import os
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
import json
import argparse
from tqdm import tqdm
from contextlib import suppress
import time

def check_redirect(response):
    if response.history:
        raise requests.HTTPError




def download_txt(url, filename, folder='books/'):
    directory = os.path.join(args.dest_folder, folder)
    Path(directory).mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    check_redirect(response)
    filename = sanitize_filename(filename) + '.txt'
    filepath = os.path.join(args.dest_folder, folder, filename)
    with open(filepath, 'w') as file:
        file.write(response.text)
    return filepath


def download_image(url, filename, folder='images/'):
    directory = os.path.join(args.dest_folder, folder)
    Path(directory).mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    check_redirect(response)
    filename = sanitize_filename(filename)
    filepath = os.path.join(args.dest_folder, folder, filename)
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def parse_book_information(url):
    response = requests.get(url)
    response.raise_for_status()
    check_redirect(response)
    response_soup = BeautifulSoup(response.text, 'lxml')

    header_element_text = response_soup.select_one('.ow_px_td h1').get_text()
    book_header = header_element_text.split('\xa0')[0].strip()
    book_author = header_element_text.split('\xa0')[2].strip()

    image_source = response_soup.select_one('.bookimage img')['src']
    image_link = urljoin(url, image_source)

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

    for page_number in range(start, end + 1):
        url = 'http://tululu.org/l55/{}/'.format(page_number)
        response = requests.get(url)
        response.raise_for_status()
        check_redirect(response)
        response_soup = BeautifulSoup(response.text, 'lxml')

        book_cards = response_soup.select('#content .d_book')

        for book in book_cards:
            book_short_link = book.select_one('a')['href']
            book_link = urljoin(url, book_short_link)
            book_id = book_short_link[2:-1]
            science_fiction_books_links.append((book_link, book_id))

    return science_fiction_books_links


def parse_console_arguments():
    parser = argparse.ArgumentParser(description='Парсинг книг из онлайн библиотеки.')
    parser.add_argument('-s', '--start_page', help='Начальная страница', default=1, type=int)
    parser.add_argument('-e', '--end_page', help='Конечная страница', default=1, type=int)
    parser.add_argument('-df', '--dest_folder', help='Путь к каталогу с рез-тами парсинга.', default='')
    parser.add_argument('-jp', '--json_path', help='Путь к файлу с JSON данными.', default='')
    parser.add_argument('-si', '--skip_img', help='Не скачивать обложки.', action='store_false')
    parser.add_argument('-st', '--skip_txt', help='Не скачивать книги.', action='store_false')
    return parser


if __name__ == '__main__':
    parser = parse_console_arguments()
    args = parser.parse_args()

    try:
        science_fiction_books_links = get_books_links(args.start_page, args.end_page)
    except requests.HTTPError:
        print('Указаны некорректные номера страниц, попробуйте еще раз!')
        exit(1)

    books_information = []

    for link, id in tqdm(science_fiction_books_links):
        try:
            book_information = parse_book_information(link)


            if args.skip_txt:
                txt_url = 'http://tululu.org/txt.php?id={}'.format(id)
                book_name = '{}. {}'.format(id, book_information['title'])
                book_information['book_path'] = download_txt(txt_url, book_name)

            if args.skip_img:
                book_source = book_information['image_src']
                image_filename = book_source.split('/')[-1]
                book_information['image_src'] = download_image(book_source, image_filename)

            books_information.append(book_information)
        except (requests.HTTPError, ConnectionError):
            print('Ошибка! Проверьте ваше подключение к интернету. Следующая автоматическая попытка через 3 секунды..')
            time.sleep(3)
            continue



    if not args.json_path:
        json_filepath = os.path.join(args.dest_folder, 'books_information.json')
        Path(args.dest_folder).mkdir(parents=True, exist_ok=True)
    else:
        json_filepath = os.path.join(args.json_path, 'books_information.json')
        Path(args.json_path).mkdir(parents=True, exist_ok=True)

    with open(json_filepath, 'w', encoding='utf-8') as file:
        json.dump(books_information, file, ensure_ascii=False, indent=2)

