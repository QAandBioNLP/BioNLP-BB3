import argparse
import io
import re
import codecs


################################################################################
# This code is written by Helen Cook, with contributions from Lars Juhl Jensen
# and Vangelis Pafilis, as part of the BioNLP 2016 contest. 
# 
# Distributed under BSD License.
################################################################################

def parse_input(inputfile):
    # Input format is one abstract per file, title and abstract are on separate lines
    input = ""
    with codecs.open(inputfile, encoding='utf-8') as f:
        for line in f:
            input += line
    f.close()
    return input

def parse_coords(a1file):
    # one line for each entity
    coords = []
    with codecs.open(a1file, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip("\n")
            if "\tBacteria" in line or "\tHabitat" in line:
                text_id, col, string = line.split("\t")
                try:
                    text_type, start, end = col.split(" ")
                    coords.append((int(start), int(end), string))
                except:
                    print "ignoring multi position " + line
                    pass
    f.close()
    return coords

def compare(document, coords, filename):
    count = 0
    for coord in coords:
        start, end, string = coord
        doc_string = document[start:end]
        #print ">" + doc_string + "< >" + string + "<"
        if string != doc_string:
            count += 1
            print "coords " + str(start) + " " + str(end) + " in " + filename + " are >" + doc_string + "< not >" + string + "<"
    print str(count) + " coords were inconsistent in " + filename

def main():
    parser = argparse.ArgumentParser(description="BioNLP contest coordinate checker")
    parser.add_argument('-f', '--file',
                required=True,
                dest='inputfile',
                help="input file to parse")
    
    args=parser.parse_args()

    if args.inputfile:
        document = parse_input(args.inputfile)
        coords = parse_coords(args.inputfile.replace(".txt", ".a1"))
        compare(document, coords, args.inputfile)


if __name__ == "__main__":
    main()
