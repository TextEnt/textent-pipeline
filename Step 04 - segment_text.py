from lxml import etree
from transformers import pipeline
import glob
import re
import os
import tqdm
import random
from operator import itemgetter
import shutil

BATCH_SIZE=8
ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
normaliser = pipeline(model="rbawden/modern_french_normalisation", batch_size=BATCH_SIZE, beam_size=5, cache_file="./cache.pickle", trust_remote_code=True)

# SEGMENTATION ################################################################

def rebuild_words(doc):
    """
    Used to rebuild a word separated by a lb element.
    For example :
    <lb/>I hope this script is use
    <lb break='no' rend='-'/>ful
    will give :
    <lb/>I hope this script is useful
    --> then all words can be tokenized correctly.

    :param doc: a XML document
    :return: the same document with rebuilt word.
    :rtype: a new XLM document
    """
    # For each line break wich splits a word in two, we want to remove it and reform the word.
    for lb in doc.xpath("//tei:lb[@break='no']", namespaces=ns):
        # We get the text where the first part of the word belongs.
        previous = lb.getprevious()
        # We get the second part.
        tail = lb.tail if lb.tail is not None else ""
        # We want to be sure that the element contains a string and we want to be sure that there is some text.
        # This prevents encoding errors.
        if previous != None and previous.tail != None:
            previous.tail = previous.tail.rstrip() + tail
        # Otherwise, we get the text of the parent element and we want to be sure that there is some text.
        elif lb.getparent().tail != None :
            lb.getparent().text = lb.getparent().text.rstrip() + tail
        lb.getparent().remove(lb)


def transform_text(doc):
    """
    This function removes unsupported tags from a given doc.

    :param doc: XML document
    :return: XML doc after transformation
    :rtype: XLM doc
    """
    xslt = etree.parse('XSLT/clean_text.xsl')
    transform = etree.XSLT(xslt)
    doc_transf = transform(doc)
    return doc_transf

def segment(doc):
    """
    For each lines and paragraphs, this function segments the text.

    :param doc: a XML document
    :return: a level 3 XML document
    :rtype: a new XLM document
    """
    # Only the text enclosed between <p> and <l> is segmented.
    paragraphs = doc.xpath('//tei:text//tei:p', namespaces=ns)
    speeches = doc.xpath('//tei:body//tei:ab', namespaces=ns)
    segment_elements(paragraphs)
    segment_elements(speeches)
    # This output file is specific to the project e-ditiones, you can easily change the output with e.g. doc.write("New" + args.file, ...)
    add_orig(doc)


def segment_elements(list_elements):
    """
    For each element, this function adds the text in the new <seg> elements.

    :param doc: a list of XML elements
    """
    for element in list_elements:
        text = element.text
        segs = segment_text(text)
        # This removes the text before we add it in the new <seg> element.
        element.clear()
        element.extend(segs)

def segment_text(text):
    """
    This function is used to segment the text and wrap these segments with <seg> elements.

    :param doc: text
    :return: a list of segments
    :rtype: list
    """
    if re.findall(r"[^\.\?:\;!]+[\.\?:\;!]?", text)!= None:
        segments = re.findall(r"[^\.\?:\;!]+[\.\?:\;!]?", text)
        list = []
        n = 1
        for segment in segments:
            # This makes sure no <seg> is empty
            text = segment.strip()
            if text:
                seg = etree.Element("{http://www.tei-c.org/ns/1.0}seg")
                seg.text = text
                seg.attrib["n"] = str(n)
                # The xml:id attribute is generated with the value of the n attribute.
                seg.attrib["{http://www.w3.org/XML/1998/namespace}id"] = "s" + seg.get("n")
                n += 1
                list.append(seg)
    return list

def add_orig(doc):
    """
    This function duplicates the content of <seg> in a <orig> and a <reg>

    :param doc: XML document
    :return: XML doc after transformation
    :rtype: XLM doc
    """
    xslt = etree.parse('XSLT/clean_origReg.xsl')
    transform = etree.XSLT(xslt)
    doc_transf = transform(doc)
    normalise(doc_transf)
    #print(doc_transf)
    return doc_transf.write(file.replace(".xml", "_segmented.xml"), pretty_print=True, encoding="utf-8", method="xml")

def normalise(xml_doc, batch_size: int = BATCH_SIZE, debug: bool = True):
    """
    This function normalises the text

    :param doc: XML document
    :return: XML doc after normalisation
    :rtype: XLM doc
    """
    origs = xml_doc.xpath('//tei:orig', namespaces=ns)
    regs = xml_doc.xpath('//tei:reg', namespaces=ns)

    pbar = tqdm.tqdm(total=len(regs))
    #remove some signs at the beginning of the line to avoid crash
    clean_start = re.compile(r"^([\s\-\(\)'\"]+)")

    #processing the origs
    for orig in origs:
        orig_corr=clean_start.sub('',orig.text.replace('\n', ' '))
        orig.text=orig_corr

    #processing regs
    for i in range(0, len(regs), batch_size):
        # Get the batch x
        current_batch = regs[i:i + batch_size]
        #clean batch + rm newlines
        current_batch_as_text = [
            clean_start.sub('',current_reg.text.replace('\n', ' '))
            for current_reg in current_batch
        ]
        try:
            #normalise
            normed_batch = normaliser(current_batch_as_text)
            for current_reg, current_norm, current_text in zip(current_batch, normed_batch, current_batch_as_text):
                #text is in a dict with value "text"
                current_reg.text = current_norm.get("text", "<ERROR>")
                #replace in the node
                current_norm = current_reg.text
                pbar.update(1)
                #show a transformation 10% of the time (randomly)
                if debug and random.random() < .1:
                    pbar.set_description(f"{current_text[:20]} => {current_norm[:20]}")
        #if problen while normalising
        except Exception as E:
            print(E)
            print(current_batch_as_text)
            raise E

if __name__ == "__main__":
    #XML parser
    parser = etree.XMLParser(remove_blank_text=True)
    #file dir
    files = glob.glob("in_XML/**/*", recursive=True)
    #loop over files
    for file in files:
        print(file)
        doc = etree.parse(file, parser)
        #added <xsl:template match="tei:lb"/> instead in xslt
        #rebuild_words(doc)
        text_transformed = transform_text(doc)
        segment(text_transformed)
    # Check if folder exists to store results
    data_dir = os.path.join("origReg")
    #if not make it
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    #move all processed files to the new dir
    files = glob.iglob(os.path.join("in_XML", "*segmented.xml"))
    for file in files:
        if os.path.isfile(file):
            filename=os.path.basename(file)
            print(filename)
            shutil.move(os.path.join("in_XML",filename),os.path.join(data_dir,filename))
