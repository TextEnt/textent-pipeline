from lxml import etree
from flair.models import SequenceTagger
from flair.data import Sentence
import os
import glob
import tqdm
import shutil
import html

ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
tagger_path = os.path.join("models","final-model.pt")
tagger = SequenceTagger.load(tagger_path)

TAGGED_ENTITY = "<{label}  xmlns=\"http://www.tei-c.org/ns/1.0\">{entity}</{label}>"

def recognize(xml_doc, debug: bool = True):
    """
    This function normalises the text

    :param doc: XML document
    :return: XML doc after normalisation
    :rtype: XLM doc
    """
    regs = xml_doc.xpath('//tei:reg', namespaces=ns)

    pbar = tqdm.tqdm(total=len(regs))
    #remove some signs to avoid crash

    for reg in regs:
        #get rid of carriage returns and replace it by space
        try:
            reg_text=reg.text
            #print("INPUT: ", reg_text)
            sentence = Sentence(reg_text)
            #print("SENTENCED: ", sentence)
            #print("TYPE", type(sentence))
            tagger.predict(sentence)
            #print("TAGGED: ", sentence.to_tagged_string())
            tagged_sentence= split_to_spans(sentence)
            spans = split_to_spans(sentence)
            #print("SPANS: ", spans)
            spans_xml = []
            for fragment, tag in spans:
                #print("TAG: ", tag)
                #print("FRAGMENT: ",fragment)
                escaped_fragment = html.escape(fragment)
                #print("ESCAPED_FRAGMENT: ",escaped_fragment)
                if tag:
                    escaped_fragment = TAGGED_ENTITY.format(
                        entity=escaped_fragment,
                        label=tag,
                    )
                spans_xml.append(escaped_fragment)
            final_text = etree.XML("<reg xmlns=\"http://www.tei-c.org/ns/1.0\">"+"".join(spans_xml)+"</reg>")
            reg.getparent().replace(reg, final_text)
            #print("NODE: ", etree.tostring(reg))
        except Exception as E:
            print("IS NOT TAGGED: ", sentence)
            print(E)
            raise E
        pbar.update(1)
    return xml_doc
        

def split_to_spans(s: Sentence, label_name="ner"):
    orig = s.to_original_text()
    last_idx = 0
    spans = []
    tagged_ents = s.get_labels(label_name)
    for ent in tagged_ents:
        if last_idx != ent.data_point.start_position:
            spans.append((orig[last_idx : ent.data_point.start_position], None))
        spans.append((ent.data_point.text, ent.value))
        assert ent.data_point.end_position is not None
        last_idx = ent.data_point.end_position
    if last_idx < len(orig) - 1:
        spans.append((orig[last_idx : len(orig)], None))
    return spans

def TEIsation(xml_doc):
    """
    This function removes unsupported tags from a given doc.

    :param doc: XML document
    :return: XML doc after transformation
    :rtype: XLM doc
    """
    xslt = etree.parse('XSLT/clean_NER.xsl')
    transform = etree.XSLT(xslt)
    doc_transf = transform(xml_doc)
    return doc_transf.write(file.replace(".xml", "_ner.xml"), pretty_print=True, encoding="utf-8", method="xml", xml_declaration=True)


if __name__ == "__main__":
    parser = etree.XMLParser(remove_blank_text=True)
    files = glob.glob("origReg/**/*", recursive=True)
    for file in files:
        print(file)
        doc = etree.parse(file, parser)
        recognize(doc)
        TEIsation(doc)
    # Check if folder exists to store results
    data_dir = os.path.join("NER")
    #if not make it
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    #move all processed files to the new dir
    files = glob.iglob(os.path.join("origReg", "*_ner.xml"))
    for file in files:
        if os.path.isfile(file):
            filename=os.path.basename(file)
            print(filename)
            shutil.move(os.path.join("origReg",filename),os.path.join(data_dir,filename))