import argparse

parser = argparse.ArgumentParser(description='Convert original textent metadata to ladas2tei format.')
parser.add_argument('input', metavar='IN', type=str, 
                    help='source metadata file')
parser.add_argument('output', metavar='OUT', type=str, 
                    help='output metadata file')
args = parser.parse_args()

with open(args.input, 'r', encoding='utf-8') as f:
    lines = [line.split() for line in f.readlines()]

print(lines[10])