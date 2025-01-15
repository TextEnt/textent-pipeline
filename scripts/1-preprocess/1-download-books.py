import requests
import argparse
import os
import time

def download_one_page(url):
    # try to download the image 10 times before returning the error code
    image = requests.get(url)
    tried = 1
    time_to_wait = 40
    while image.status_code != 200:
        image = requests.get(url)
        tried += 1
        if image.status_code != 200:
            if tried == 10:
                return (image.status_code, None)
            print("HTTP code " + str(image.status_code) + " while downloading " + url + ". Retrying in " + str(time_to_wait) + " seconds...")
            time_to_wait += 10
            time.sleep(time_to_wait)
    return 200, image


def download_books(output_folder, urls):
    number_of_try = 100
    for i in range(number_of_try):
        try:
            # create a directory for each book
            # download each page of each book
            # if not http 200, return the error code
            try:
                with open("downloaded_books.txt", "r") as file:
                    print("Remove previously downloaded books from the list.")
                    downloaded_books = file.read().split()
                    urls = [url for url in urls if url not in downloaded_books]
            except FileNotFoundError:
                print("No previously downloaded books.")
            print("Remaining books to download: " + str(len(urls)))
            cpt_books = 0
            for url in urls:
                book_name = url.split('/')[-1]
                try:
                    os.mkdir(output_folder + '/' + book_name)
                except FileExistsError:
                    print("Folder " + output_folder + '/' + book_name + " already exists.")
                cpt_pages = 1
                current_url = url+"/f"+str(cpt_pages)+".highres"
                print("Downloading " + current_url + "...")
                http_code, image = download_one_page(current_url)
                if(http_code != 200):
                    return http_code
                new_url = url+"/f"+str(cpt_pages+1)+".highres"
                print("Downloading " + new_url + "...")
                http_code, new_image = download_one_page(new_url)
                if(http_code != 200):
                    return http_code
                # no proper error code, must download until content stay the same
                while image.content != new_image.content:
                    output_filename = output_folder + '/' + book_name + '/' + str(cpt_pages) + '.jpg'
                    with open(output_filename, 'wb') as f:
                        f.write(image.content)
                    cpt_pages += 1
                    image = new_image
                    new_url = url+"/f"+str(cpt_pages+1)+".highres"
                    print("Downloading " + new_url + "...")
                    http_code, new_image = download_one_page(new_url)
                    if(http_code != 200):
                        return http_code
                output_filename = output_folder + '/' + book_name + '/' + str(cpt_pages) + '.jpg'
                with open(output_filename, 'wb') as f:
                        f.write(image.content)
                cpt_books += 1
                print("=== Downloaded " + str(cpt_books) + " books out of " + str(len(urls)) + " ===")
                with open("downloaded_books.txt", "a") as file:
                    file.write(url+"\n")
        except Exception as e:
            print("Error while downloading books: " + str(e))
            print("Try number " + str(i))
            print("Retrying (max " + str(number_of_try) + " times in total)...")

    return 200

def get_books_urls(input_metadata, column):
    # extract the last token of each line as URL except first line
    with open(input_metadata, 'r') as metadata_file:
        urls = list(set([line.split()[column] for line in metadata_file.readlines()[1:]]))
    return urls

parser = argparse.ArgumentParser(description='Download books from a metadata file.')
parser.add_argument('input', metavar='IN', type=str, 
                    help='source metadata file')
parser.add_argument('output', metavar='OUT', type=str, 
                    help='folder where files are stored')
args = parser.parse_args()

column = -1
urls = get_books_urls(args.input, column)

try:
    os.mkdir(args.output)
except FileExistsError:
    print("Folder " + args.output + " already exists.")

ret = download_books(args.output, urls)

if ret != 200:
    print("HTTP code " + str(ret) + " returned.")
else:
    print("Download successful.")

