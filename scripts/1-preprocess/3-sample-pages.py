# Give a folder of books to this script and a number of pages
# It will extract the given number of pages from all the books
# and store them in a new folder

import argparse

parser = argparse.ArgumentParser(description='Extract pages from bookks folder.')
parser.add_argument('input', metavar='IN', type=str, 
                    help='source folder')
parser.add_argument('output', metavar='OUT', type=str, 
                    help='destination folder')
parser.add_argument('number', metavar='NUM', type=int, 
                    help='number of pages to extract')
args = parser.parse_args()

# get the number of books in source folder
import os
books = os.listdir(args.input)
n_books = len(books)
# compute every nth book to extract
step = max(n_books // args.number, 1)
for i in range(0, n_books, step):
    book = books[i]
    # copy one random page from the book to the destiation folder
    import random
    pages = os.listdir(args.input + '/' + book)
    page = random.choice(pages)
    os.system('cp ' + args.input + '/' + book + '/' + page + ' ' + args.output + '/' + book + '_' + page)