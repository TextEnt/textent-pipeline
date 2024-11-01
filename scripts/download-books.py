import requests
import argparse
import os

def download_one_page(url):
    image = requests.get(url)
    if image.status_code == 429:
        print("Too many requests")
        print(image.headers)
        exit(0)
    return image


def download_books(output_folder, urls):
    # create a directory for each book
    # manage 429 codes (too many requests)
    for url in urls:
        book_name = url.split('/')[-1]
        try:
            os.mkdir(output_folder + '/' + book_name)
        except FileExistsError:
            print("Folder " + output_folder + '/' + book_name + " already exists.")
        cpt = 1
        current_url = url+"/f"+str(cpt)+".highres"
        print("Downloading " + current_url + "...")
        image = download_one_page(current_url)
        new_url = url+"/f"+str(cpt+1)+".highres"
        print("Downloading " + new_url + "...")
        new_image = download_one_page(new_url)
        # no proper error code, must download until content stay the same
        while image.content != new_image.content:
            with open(output_folder + '/' + book_name + '/' + str(cpt) + '.jpg', 'wb') as f:
                f.write(image.content)
            cpt += 1
            image = new_image
            new_url = url+"/f"+str(cpt+1)+".highres"
            print("Downloading " + new_url + "...")
            new_image = download_one_page(new_url)
        with open(output_folder + '/' + book_name + '/' + str(cpt) + '.jpg', 'wb') as f:
                f.write(image.content)

def get_books_urls(input_metadata):
    # extract the last token of each line as URL except first line
    with open(input_metadata, 'r') as metadata_file:
        urls = list(set([line.split()[-1] for line in metadata_file.readlines()[1:]]))
    return urls

parser = argparse.ArgumentParser(description='Download books from a metadata file.')
parser.add_argument('input', metavar='IN', type=str, 
                    help='source metadata file')
parser.add_argument('output', metavar='OUT', type=str, 
                    help='folder where files are stored')
args = parser.parse_args()

urls = get_books_urls(args.input)
try:
    os.mkdir(args.output)
except FileExistsError:
    print("Folder " + args.output + " already exists.")
download_books(args.output, urls)

