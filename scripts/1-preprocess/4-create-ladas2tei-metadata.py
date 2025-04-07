import argparse
import pprint
from bs4 import BeautifulSoup
import requests

def reformat_erara_url(url):
    if "https://" in url:
        return url
    if "doi:" in url:
        url = "https://www.doi.org/"+url.split(":")[1]
        return url
    return "https://"+url

parser = argparse.ArgumentParser(description='Convert original textent metadata to ladas2tei format.')
parser.add_argument('input', metavar='IN', type=str, 
                    help='source metadata file')
parser.add_argument('output', metavar='OUT', type=str, 
                    help='output metadata file')
args = parser.parse_args()

with open(args.input, 'r', encoding='utf-8') as f:
    lines = [line.split("\t") for line in f.readlines()]


l2t_lines = []
i = 1
for line in lines:
    if "gallica.bnf.fr" in line[1]:
        folder_name = line[1].split('/')[-1]
        newline = [folder_name, str(i), line[17], line[14], line[15], line[19]]
        print(f"{i}/{len(lines)} - adding gallica book {folder_name}")
        i += 1
        l2t_lines.append(newline)
    elif "doi" in line[1] and "e-rara" in line[1]:
        url = reformat_erara_url(line[1])
        print(f"requesting {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a['href'] for a in soup.find_all('a', href=True) if "i3f" in a['href'] and "index.html" not in a['href']]
        i3f_manifest_url = "https://www.e-rara.ch"+links[0]
        folder_name = "doi_"+url.split("/")[3]+"_"+url.split("/")[4]+"_"+i3f_manifest_url.split("/")[5]
        newline = [folder_name, str(i), line[17], line[14], line[15], line[19]]
        print(f"{i}/{len(lines)} - adding erara book {folder_name}")
        i += 1
        l2t_lines.append(newline)
    elif "https://numelyo.bm-lyon.fr" in line[1]:
        folder_name = "numelyo_"+line[1].split("/")[4].split(":")[0]+"_"+line[1].split("/")[4].split(":")[1]
        newline = [folder_name, str(i), line[17], line[14], line[15], line[19]]
        print(f"{i}/{len(lines)} - adding numelyo book {folder_name}")
        i += 1
        l2t_lines.append(newline)
    elif "https://tolosana.univ-toulouse.fr" in line[1]:
        book_number = line[1].split("/")[-1]
        folder_name = "tolosana_"+book_number
        newline = [folder_name, str(i), line[17], line[14], line[15], line[19]]
        print(f"{i}/{len(lines)} - adding tolosana book {folder_name}")
        i += 1
        l2t_lines.append(newline)

    

#pprint.pp(l2t_lines[0:10])


with open(args.output, 'w', encoding='utf-8') as f:
    f.write("file_name,number,title,date,author,publisher\n")
    for line in l2t_lines:
        f.write("\t".join(line)+"\n")