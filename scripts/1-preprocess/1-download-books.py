import requests
import argparse
import os
import time
from bs4 import BeautifulSoup

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


def download_gallica(output_folder, url):
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
    return 200

def reformat_erara_url(url):
    if "https://" in url:
        return url
    if "doi:" in url:
        url = "https://www.doi.org/"+url.split(":")[1]
        return url
    return "https://"+url

def download_erara(output_folder, url):
    print(url)
    response = requests.get(url)
    if response.status_code != 200:
        print("Error code "+str(response.status_code)+" while downloading "+url)
        return response.status_code

    soup = BeautifulSoup(response.text, "html.parser")
    links = [a['href'] for a in soup.find_all('a', href=True) if "i3f" in a['href'] and "index.html" not in a['href']]
    if len(links) != 1:
        print("Error extracting iiif manifest from erara page")
        return 0
    i3f_manifest_url = "https://www.e-rara.ch"+links[0]
    print("manifest url: "+i3f_manifest_url)
    response = requests.get(i3f_manifest_url)
    if response.status_code != 200:
        print("Error code "+str(response.status_code)+" while downloading "+url)
        return response.status_code
    manifest = response.json()
    images = []
    try:
        canvases = manifest["sequences"][0]["canvases"]
        images = [canvas["images"][0]["resource"]["@id"] for canvas in canvases]
    except (KeyError, IndexError) as e:
        print(f"Error extracting images: {e}")
        return 0
    book_folder = output_folder+"/doi_"+url.split("/")[3]+"_"+url.split("/")[4]+"_"+i3f_manifest_url.split("/")[5]
    try:
        os.mkdir(book_folder)
    except FileExistsError:
        print("Folder " + book_folder + " already exists.")
    for i, img_url in enumerate(images):
        print("Downloading "+img_url+" from "+url)
        #img_response = requests.get(img_url, stream=True)
        status_code, img_response = download_one_page(img_url)
        if status_code == 200:
            img_path = os.path.join(book_folder, f"{i+1}.jpg")
            with open(img_path, "wb") as file:
                for chunk in img_response.iter_content(1024):
                    file.write(chunk)
        else:
            print(f"Failed to download {img_url}, error code {status_code}")
            return status_code

    return 200

def numelyo_title_contains_404(image):
    try:
        soup = BeautifulSoup(image.text, "html.parser")
        title = soup.title.string if soup.title else ""
        return "404 Not Found" in title
    except Exception as e:
        # yeah ... probably an image ...
        return False


def download_one_page_numelyo(base_url, i):
    # try TIF format
    url = base_url+f"/web_TIF{i:08d}.jpg"
    image = requests.get(url)
    if not numelyo_title_contains_404(image):
        if image.status_code == 200:
            print(url)
            return 200, image
        # image exist, but timeout or other, retry
        return download_one_page(url)
    # not TIF, try JPG
    url = base_url+f"/web_JPG{i:08d}.jpg"
    image = requests.get(url)
    if not numelyo_title_contains_404(image):
        if image.status_code == 200:
            print(url)
            return 200, image
        # image exist, but timeout or other, retry
        return download_one_page(url)
    
    return 404, None


def download_numelyo(output_folder, url):
    base_url = url.replace("f_view", "f_eserv")
    status_code = 200
    i = 1
    book_folder = output_folder+"/numelyo_"+url.split("/")[4].split(":")[0]+"_"+url.split("/")[4].split(":")[1]
    try:
        os.mkdir(book_folder)
    except FileExistsError:
        print("Folder " + book_folder + " already exists.")
    while status_code != 404:
        print(f"Downloading {base_url} page {i}")
        status_code, img_response = download_one_page_numelyo(base_url, i)
        if status_code==404:
            print(f"Done downloading {i-1} pages")
            return 200
        if status_code == 200:
            img_path = os.path.join(book_folder, f"{i}.jpg")
            with open(img_path, "wb") as file:
                for chunk in img_response.iter_content(1024):
                    file.write(chunk)
        else:
            print(f"Failed to download {img_url}, error code {status_code}")
            return status_code
        i += 1
    

def download_books(output_folder, urls):
    number_of_try = 2
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
                if "gallica.bnf.fr" in url:
                    ret_code = download_gallica(output_folder, url)
                    if ret_code != 200:
                        return ret_code
                    cpt_books += 1
                    print("=== Downloaded " + str(cpt_books) + " books out of " + str(len(urls)) + " ===")
                    with open("downloaded_books.txt", "a") as file:
                        file.write(url+"\n")
                elif "doi" in url and "e-rara" in url:
                    proper_url = reformat_erara_url(url)
                    ret_code = download_erara(output_folder, proper_url)
                    if ret_code != 200:
                        return ret_code
                    cpt_books += 1
                    print("=== Downloaded " + str(cpt_books) + " books out of " + str(len(urls)) + " ===")
                    with open("downloaded_books.txt", "a") as file:
                        file.write(url+"\n")
                elif "https://numelyo.bm-lyon.fr" in url:
                    ret_code = download_numelyo(output_folder, url)
                    if ret_code != 200:
                        return ret_code
                    cpt_books += 1
                    print("=== Downloaded " + str(cpt_books) + " books out of " + str(len(urls)) + " ===")
                    with open("downloaded_books.txt", "a") as file:
                        file.write(url+"\n")
                else:
                    print("(unable to download) book url : "+url)
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
parser.add_argument('column', metavar='COL', type=int, 
                    help='column containing URL in metadata file')
args = parser.parse_args()

urls = get_books_urls(args.input, args.column)

try:
    os.mkdir(args.output)
except FileExistsError:
    print("Folder " + args.output + " already exists.")

ret = download_books(args.output, urls)

if ret != 200:
    print("HTTP code " + str(ret) + " returned.")
else:
    print("Download successful.")

