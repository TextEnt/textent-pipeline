import argparse

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
    newline = [line[1], i, line[17], line[14], line[15], line[19]]
    l2t_lines.append(newline)
    i += 1


print(l2t_lines[10])