from tagger import *
import argparse
import io
import re
import codecs
import sys
from operator import add


################################################################################
# This code is written by Helen Cook, with contributions from Lars Juhl Jensen
# and Vangelis Pafilis, as part of the BioNLP 2016 contest. 
# 
# Distributed under the BSD license. 
# Dictionary files distributed under CC BY.
################################################################################

def parse_input(inputfile):
    # Input format is one abstract per file, title and abstract are on separate lines, data is in col 3
    input = ""
    tindex = 0
    with open(inputfile, 'r') as f:
        for line in f:
            cols = line.split("\t")
            input += cols[2]
            tindex = cols[0].lstrip("T")
    f.close()
    return input, tindex

def parse_a2(inputprefix):
    normalization = {}
    annotated = []
    spaces_regex = re.compile('\s+')

    # store the normalizations from a2
    with open(inputprefix + ".a2") as f:
        for line in f:
            cols = spaces_regex.split(line)
            if cols[0].startswith("N"): 
                referent = cols[3].lstrip("Referent:")
                annot = cols[2].lstrip("Annotation:")
                if annot in normalization:
                    normalization[annot].append(referent)
                else:
                    normalization[annot] = [referent]

    # combine with the tags 
    with open(inputprefix + ".a2") as f:
        for line in f:
            cols = spaces_regex.split(line)
            if cols[0].startswith("T"):
                entity = ''
                if cols[1] == "Bacteria":
                    entity = -2
                if cols[1] == "Habitat":
                    entity = -20
                start = 0
                end = 0
                if entity:
                    if ";" in cols[3]:
                        # this is a multiposition match, which the tagger does not search for
                        start = int(cols[2])
                        end = int(cols[4])
                    else:
                        start = int(cols[2])
                        end = int(cols[3])
                    entities = []
                    for norm in normalization[cols[0]]:
                        entities.append((entity, norm))
                    annotated.append((start, end, tuple(entities)))
    return annotated

def convert_results(results, document):
    u_results = []
    # for each byte in the document, determine if it belongs to a multi byte character
    mapping = {} # byte to char
    byte = 0
    character = 0
    u_document = document.decode("utf-8") # turn bytes into characters
    for b in u_document:
        u = b.encode('utf-8') # back to bytes
        char_bytes = len(u) # how many bytes does this character consist of
        for i in range(0, char_bytes):
            mapping[byte+i] = character
        byte += char_bytes
        character += 1  

    for result in results:
        start, end, entity_list = result
        u_results.append((mapping[start], mapping[end], entity_list))

    return u_results, u_document

def is_bacteria(result):
    start, end, entitylist = result
    # check that at least one entity type associated with this result is a bacteria
    is_bacteria = False
    for entity in entitylist:
        entity_type, entity_id = entity
        if int(entity_type) == -2:
            is_bacteria = True
    return is_bacteria

def insert_in_order(results, entrant):
    # put the new entrant into the right place in the results array according to start position
    new_start, new_end, new_list = entrant
    new_results = []
    added = False
    for res in results:
        start, end, entitylist = res
        if coords_overlap(start, end, new_start, new_end):
            # skip adding this entrant because it will overlap an existing term
            added = True 
        if (new_start < start and new_end < start) and not added:
            new_results.append(entrant)
            added = True
        new_results.append(res)
    if not added:
        new_results.append(entrant)
    return new_results

def string_to_bytes(text, charset="utf8"):
    if isinstance(text, unicode):
        byte_array = None
        for tolerance in ("strict", "replace", "ignore"):
            try:
                return text.encode(charset, tolerance)
            except UnicodeEncodeError:
                pass
            raise Exception, "Unable to convert unicode string to a byte-array!"
    else:
        return text

def dedup_results(results):
    starts = {}
    for res in results:
        start, end, entitylist = res
        if start in starts:
            e_start, e_end, e_entitylist = starts[start]
            if end > e_end:
                starts[start] = res
        else:
            starts[start] = res

    deduped = []
    for start in sorted(starts.keys()):
        deduped.append(starts[start])
    return deduped
        
def expand_acronyms(results, document, tagger):
    max_extend = 20
    min_word_len = 3

    acronym_regex=re.compile('^\s[(](.+)[)]') # anything one or more characters long inside brackets
    space_regex = re.compile('\s')
    strain_regex = re.compile('^(species|sp\.?|subspecies|subsp\.?|ssp\.?|spp\.?|strain|str\.?|serotype|serovar|bv\.?|biovar|pv\.?|genomosp\.?|genomovar\.?|genosp\.?|cf\.?|clone|isolate|ATCC|type|var\.?)$')
    acronym_name_regex = re.compile('^[A-Z][A-z0-9:\-_]+$') # exclude parens, percent
    punc = '!"#$%&\'\*\+,\-\./:;<=>\?@\[\\]^_`{|}~()' # TODO does not include unicode punctuation
    english_regex = re.compile('^[' + punc + ']*[A-z][a-z' + punc + ']*[' + punc + ']*$')

    # build up the list of acronyms
    acronyms = []
    for result in results:
        start, end, entitylist = result
        #entity = document[start:end+1]
        entity = get_name(result, document)
        # put genus and strain of entity on the 'acronym' list if it is a bacteria
        if is_bacteria(result):
            words = space_regex.split(entity)

            for word in (words[0], words[-1]):
                if not strain_regex.search(word): # don't add strain indicators as acronyms
                    position = end
                    if len(word) >= min_word_len:
                        word = word.replace("(", "")
                        word = word.replace(")", "")
                        if not english_regex.search(word):
                            if not tagger.is_blocked(string_to_bytes(word), "0"):
                                acronyms.append((word, entitylist, position))

        # include tagging both "Three Letter Acronym" and ("TLA") in the match
        extended = document[end+1:end+max_extend+1]
        m = acronym_regex.search(extended)
        if m:
            position = end+1+m.start() # acronym is only defined for positions after this point in the document
            for acronym in m.groups():
                if acronym:
                    acronym = acronym.replace("(", "")
                    acronym = acronym.replace(")", "")
                    if acronym_name_regex.search(acronym):
                        if entity[0].lower() in acronym[0:3].lower(): # verify the acronym is related to the words it is abbreviating
                            if entity_in_array((acronym, entitylist), acronyms):
                                pass
                            else:
                                acronyms.append((acronym, entitylist, position))

    # because we might have extra results from the tagger run with all parens removed, check that there are no entities that start at the same position, if so only keep the longer one
    expanded_results = dedup_results(results)

    # find the acronyms in the document
    for acr, entitylist, position in set(acronyms):
        acr_regex = re.compile('[\s(]' + acr + '[),.\-:\s]') # anywhere it is separated by space (or like characters) from the rest of the text
        for m in acr_regex.finditer(document):
            start, end = m.span()
            if start > position: # only allow acronym after its definition
                this = (start+1, end-2, entitylist)
                expanded_results = insert_in_order(expanded_results, this)

    return expanded_results
        
def expand_strain(results, document):
    max_extend = 60 # constant to determine the max number of characters following an organism match that might be part of the strain name
    expanded_results = []

    sppunc = ':;!?).,-'
    strain_regex = re.compile('^(species|sp\.?|subspecies|subsp\.?|ssp\.?|spp\.?|strain|str\.?|serotype|serovar|bv\.?|biovar|pv\.?|genomosp\.?|genomovar\.?|genosp\.?|cf\.?|clone|isolate|ATCC|type|var\.?)[' + sppunc + ']?$')
    space_regex = re.compile('\s')
    punc = '!"#$%&\'\*\+,\-\./:;<=>\?@\[\\]^_`{|}~()' # TODO does not include unicode punctuation
    punc_space_regex = re.compile('^[' + punc + ']+[\s]+.*$')

    english_restricted_regex = re.compile('^[' + punc + ']*[a-z][a-z' + punc + ']*[' + punc + ']*$')
    english_regex = re.compile('^[' + punc + ']*[A-z][a-z' + punc + ']*[' + punc + ']*$')
    stop_perc_regex = re.compile('%')
    stop_conc_regex = re.compile('(g/)|(/m)|(/l)|(cfu/)|(CFU/)')
    stop_parens_regex = re.compile('[()]') # acronyms will be caught by acronym expansion
    acronym_regex=re.compile('[(](.+)[)]') # anything one or more characters long inside brackets

    for result in results:
        start, end, entitylist = result

        # only try to expand strain names for bacteria
        if not is_bacteria(result):
            expanded_results.append(result)
            continue

        # if the character directly after the match is puncuation followed by a space, then allow no strain expansion
        separator = document[end+1:end+4]
        if punc_space_regex.search(separator):
            expanded_results.append(result)
            continue

        # store the new expanded result
        #species = document[start:end+1]
        species = get_name(result, document)
        ext_result = [species]

        # look at the text following the match to see if it contains a strain name
        extended = document[end+1+1:end+1+max_extend] # skip the space (or dash or whatever) on the LHS, take what might contain a strain on the RHS
        newend = end
        words = space_regex.split(extended)
        in_sp = False
        count_words = 0
        sp_tmp = ""
        sp_orig = 0 # number of spaces due to punctuation
        # strain names may be multiple words long, but are never allowed to contain english words
        for word in words:
            orig_word = word

            # is the word a strain separator like sp. ?
            sp = strain_regex.search(word)
            if sp:
                in_sp = True
                word = word.rstrip(',')
                word = word.rstrip(':')
                word = word.rstrip(';')
                word = word.rstrip('!')
                word = word.rstrip('?')
                word = word.rstrip(')')
                word = word.rstrip('-')
                sp_tmp = word
                if word != orig_word:
                    sp_orig += len(orig_word) - len(word)
            else:

                # do not allow anything that looks like a concentration in percentage or mg/kg etc
                perc = stop_perc_regex.search(word)
                conc = stop_conc_regex.search(word)
                parens = stop_parens_regex.search(word)
                if perc or conc or parens:
                    break

                # if the word is now empty, skip it
                if not word:
                    continue
                
                if in_sp and sp_tmp == "type":
                    wd = english_restricted_regex.search(word)
                else:
                    wd = english_regex.search(word)
                if not wd:
                    # then it can be a strain name
                    if in_sp:
                        ext_result.append(sp_tmp)
                        newend += len(sp_tmp) + 1 + sp_orig # plus one for the space 
                        sp_tmp = ""
                        in_sp = False
                    if word:
                        if acronym_regex.search(word): # must not be an acronym to be included in the name
                            continue
                        #strip any puncutuation off the RHS of the strain match
                        orig_word = orig_word.rstrip(".")
                        orig_word = orig_word.rstrip(",")
                        orig_word = orig_word.rstrip(":")
                        orig_word = orig_word.rstrip(";")
                        orig_word = orig_word.rstrip("!")
                        orig_word = orig_word.rstrip("?")
                        orig_word = orig_word.rstrip(")")
                        orig_word = orig_word.rstrip("-")
                        ext_result.append(orig_word)
                        newend += len(orig_word) + 1
                else:
                    # done looking for a strain name
                    if in_sp:
                        # only add the strain separator "species" if something follows it, else ignore it
                        if sp_tmp == "species" or sp_tmp == "strain":
                            sp_tmp = ""
                            in_sp = False
                        else:
                            ext_result.append(sp_tmp)
                            newend += len(sp_tmp) + 1  # plus one for the space 
                            sp_tmp = ""
                            in_sp = False

                    break
    
        out = " ".join(ext_result)

        newresult = (start, newend, entitylist)
        expanded_results.append(newresult)


        same = False
        if out == species:
            same = True
    return expanded_results

def get_name_an(result, document):
    start, end, entitylist = result
    return document[start:end]

def get_name(result, document):
    start, end, entitylist = result
    return document[start:end+1]

def get_normids(result):
    # used for tests
    start, end, entitylist = result
    normids = []
    for entity in entitylist:
        entity_type, entity_id = entity
        normids.append(entity_id)
    return normids
    
def merge_results(bacteria_expanded_results, habitat_expanded_results):
    # merge the two kinds of results together
    results = bacteria_expanded_results
    for result in habitat_expanded_results:
        results = insert_in_order(results, result)
    return results

def print_results(results, document, inputfile, tindex):
    # create the files that we will output to
    out_a2 = inputfile + ".a2"
    text_index = int(tindex) + 1 # start at T3 or whatever
    norm_index = 1 # start at N1

    text = ""
    norm = ""

    # then print them
    for result in results:
        start, end, entitylist = result
        if is_bacteria(result):
            entity_type = "Bacteria"
            name = get_name(result, document)
            text += "T" + str(text_index) + "\t" + entity_type + "\t" + str(start) + "\t" + str(end + 1) + "\t" + name.encode('utf8') + "\n"
        else:
            entity_type = "Habitat"
            name = get_name(result, document)
            text += "T" + str(text_index) + "\t" + entity_type + "\t" + str(start) + "\t" + str(end + 1) + "\t" + name.encode('utf8') + "\n"
    
        for entity in entitylist:
            norm_type = "OntoBiotope"
            entity_type, entity_id = entity
            if entity_type == -2:
                norm_type = "NCBI_Taxonomy"
    
            norm += "N" + str(norm_index) + "\t" + norm_type + "\t" + "Annotation:T" + str(text_index) + "\t" + "Referent:" + str(entity_id) + "\n"
            norm_index += 1
    
        text_index += 1

    with open(out_a2, 'w') as fa2:
        fa2.write(text)
        fa2.write(norm)
    fa2.close()

    return 0

def include_dots(results, document):
    # if the tagger returns sp with no dot but there is a dot following it, then include it
    included = []
    for result in results:
        start, end, entitylist = result
        name = get_name(result, document)
        last = name.split(" ")[-1]
        strain_regex = re.compile('^(sp|subsp|ssp|spp|str|bv|pv|genomosp|genomovar|genosp|cf|var)$')
        sp = strain_regex.search(last)
        if sp:
            if document[int(end)+1:int(end)+2] == ".":
                end += 1
                included.append((start, end, entitylist))
            else:
                included.append(result)
        else:
            included.append(result)
    return included

def resolve_normalization(results):
    # each entity should resolve to the first normalization returned from the tagger
    resolved = [] # to return, pruned list
    found = set() # entity_ids that we've seen, by entity_type

    for result in results:
        start, end, entitylist = result

        for entity in entitylist:
            f = False
            entity_type, entity_id = entity
            if entity_id in found:
                resolved.append((start, end, ((entity_type, entity_id),)))
                f = True
                break

        if not f:
            entity = entitylist[0]
            entity_type, entity_id = entity
            found.add(entity_id)
            resolved.append((start, end, ((entity_type, entity_id),)))
                
    return resolved

def entity_in_array(entity, array):
    for thing in array:
        if thing == entity:
            return True
    return False

def resolve_general_norm(results, groups, genus):
    # for each term, if it is a more general instance of a specific term that has been mentioned previously, then resolve to the specific term instead
    resolved = []
    seen = {}
    for result in results:
        # only do this resolution for bacteria
        if is_bacteria(result):
            start, end, entitylist = result
            for entity in entitylist:
                entity_type, entity_id = entity
                if entity_id in seen:
                    # then we have seen specific instances of this general class before (or exactly this before)
                    if entity_id in genus:
                        resolved_ids = seen[entity_id]
                        if (-2, entity_id) in resolved_ids:  # check to normalize general terms that come after specific terms to general if the general term is mentioned before the specific term
                            resolved.append(result)
                        else:
                            resolved.append((start, end, tuple(resolved_ids))) 
                    else:
                        # if not on the list of things under genus, then don't try to fix its normalization
                        resolved.append(result) 
                else:
                    # can't do better than this, so store it
                    resolved.append(result)
                    if entity_id in groups:
                        # otherwise, no members to store because this entity does not belong to any groups (eg is a phylum)
                        for g in [entity_id] + groups[entity_id]:
                            # g, groups that this entity_id is in
                            if g in seen:
                                if entity_in_array(entity, seen[g]):
                                    # don't insert duplicates
                                    pass
                                else:
                                    seen[g].append((entity_type, entity_id))
                            else:
                                seen[g] = [(entity_type, entity_id),]

                        
    return resolved;

def coords_overlap(start1, end1, start2, end2):
    if start2 <= end1 and end2 >= start1:
        return True
    return False

def evaluate_results(results, inputprefix, document, ignore_normalization):
    inputprefix = inputprefix[:-3] # remove .a1
    annotated = parse_a2(inputprefix)
    return evaluate_results_h(results, annotated, inputprefix, document, ignore_normalization)

def evaluate_results_h(results, annotated, ip='', document='', ignore_normalization=False):
    with open(ip + ".FN", 'w') as FN:  # support Python 2.6
        with open(ip + ".FP", 'w') as FP:
            with open(ip + ".OL", 'w') as OL:
                with open(ip + ".TP", 'w') as TP:
                    with open(ip + ".NM", 'w') as NM:

                        idx_ann = 0
                        idx_tag = 0

                        bacteria_TP = 0         # identical results from tagger and in A1
                        bacteria_overlap = 0    # overlapping term tagged by tagger and present in A1
                        bacteria_FN = 0         # annotated in A1 but tagger finds nothing that overlaps with the same term
                        bacteria_FP = 0         # tagger finds an entity, but nothing is present in A1 that overlaps
                        bacteria_NM = 0         # tagger finds an entity, but the normalization is incorrect

                        habitat_TP = 0
                        habitat_overlap = 0
                        habitat_FN = 0
                        habitat_FP = 0

                        while idx_tag < len(results) and idx_ann < len(annotated):
                            start, end, entity = results[idx_tag]
                            end += 1 # fix off by one
                            name = get_name(results[idx_tag], document)

                            an_start, an_end, an_entity = annotated[idx_ann]
                            an_name = get_name_an(annotated[idx_ann], document)


                            #print "looking at " + str(results[idx_tag])
                            #print " annotaion " + str(annotated[idx_ann])

                            include_habitat = False
                            if not include_habitat:
                                if not is_bacteria(results[idx_tag]):
                                    idx_tag += 1
                                    continue
                                if not is_bacteria(annotated[idx_ann]):
                                    idx_ann += 1
                                    continue

                            if an_start == start and an_end == end:
                                if set(entity) == set(an_entity) or ignore_normalization:
                                    #matching entries
                                    if is_bacteria(results[idx_tag]):
                                        entity_type = "Bacteria"
                                        bacteria_TP += 1
                                        TP.write(entity_type + "\t" + str(start) + "\t" + str(end ) + "\t" + name.encode('utf8') + "\n")
                                    else:
                                        entity_type = "Habitat"
                                        habitat_TP += 1
                                else:
                                    if is_bacteria(results[idx_tag]):
                                        #coords match but normalized wrong bacteria
                                        entity_type = "Bacteria"
                                        #bacteria_FP += 1
                                        #bacteria_FN += 1
					bacteria_NM += 1
                                        #FP.write(entity_type + "\t" + str(start) + "\t" + str(end ) + "\t" + name.encode('utf8') + "\n")
                                        #FN.write(entity_type + "\t" + str(an_start) + "\t" + str(an_end) + "\t" + an_name.encode('utf8') + "\n")
                                        NM.write(entity_type + "\t" + str(results[idx_tag]) + "\t" + name.encode('utf8') + "\t" + str(annotated[idx_ann]) + "\t" + an_name.encode('utf8') + "\n")
                                    else:
                                        #coords match but normalized wrong habitat
                                        entity_type = "Habitat"
                                        habitat_FP += 1
                                        habitat_FN += 1
                                idx_tag += 1
                                idx_ann += 1
                            elif coords_overlap(start, end, an_start, an_end):
                                if set(entity) == set(an_entity) or ignore_normalization:
                                    #overlapping entries
                                    if is_bacteria(results[idx_tag]):
                                        entity_type = "Bacteria"
                                        bacteria_overlap += 1
                                        OL.write("actual: " + entity_type + "\t" + str(start) + "\t" + str(end ) + "\t" + name.encode('utf8') + "\n")
                                        OL.write("expect: " + entity_type + "\t" + str(an_start) + "\t" + str(an_end ) + "\t" + an_name.encode('utf8') + "\n")
                                    else:
                                        entity_type = "Habitat"
                                        habitat_overlap += 1
                                else:
                                    #coords overlap but normalized don't match
                                    if is_bacteria(results[idx_tag]):
                                        entity_type = "Bacteria"
                                        #bacteria_FP += 1
                                        #bacteria_FN += 1
                                        bacteria_NM += 1
                                        #FP.write(entity_type + "\t" + str(start) + "\t" + str(end ) + "\t" + name.encode('utf8') + "\n")
                                        #FN.write(entity_type + "\t" + str(an_start) + "\t" + str(an_end) + "\t" + an_name.encode('utf8') + "\n")
                                        NM.write(entity_type + "\t" + str(results[idx_tag]) + "\t" + name.encode('utf8') + "\t" + str(annotated[idx_ann]) + "\t" + an_name.encode('utf8') + "\n")
                                    else:
                                        entity_type = "Habitat"
                                        habitat_FP += 1
                                        habitat_FN += 1
                                idx_tag += 1
                                idx_ann += 1
                            else:
                                # don't match or overlap
                                if start > an_start:
                                    # annotated entity was missed by tagger
                                    if is_bacteria(annotated[idx_ann]):
                                        entity_type = "Bacteria"
                                        bacteria_FN += 1
                                        FN.write(entity_type + "\t" + str(an_start) + "\t" + str(an_end) + "\t" + an_name.encode('utf8') + "\n")
                                    else:
                                        entity_type = "Habitat"
                                        habitat_FN += 1
                                    idx_ann += 1
                                elif an_start > start:
                                    # tagger tagged something not in the annotated file
                                    if is_bacteria(results[idx_tag]):
                                        entity_type = "Bacteria"
                                        bacteria_FP += 1
                                        FP.write(entity_type + "\t" + str(start) + "\t" + str(end ) + "\t" + name.encode('utf8') + "\n")
                                    else:
                                        entity_type = "Habitat"
                                        habitat_FP += 1
                                    idx_tag += 1
                                else:
                                    print "Warning: this should not happen."


                        # then count anything left at the end of the longer list
                        while idx_tag < (len(results)):
                            start, end, entity = results[idx_tag]
                            end += 1 # fix off by one
                            name = get_name(results[idx_tag], document)
                            if is_bacteria(results[idx_tag]):
                                entity_type = "Bacteria"
                                bacteria_FP += 1
                                FP.write(entity_type + "\t" + str(start) + "\t" + str(end ) + "\t" + name.encode('utf8') + "\n")
                            else:
                                entity_type = "Habitat"
                                habitat_FP += 1
                            idx_tag += 1

                        while idx_ann < (len(annotated)):
                            an_start, an_end, an_entity = annotated[idx_ann]
                            an_name = get_name_an(annotated[idx_ann], document)
                            if is_bacteria(annotated[idx_ann]):
                                entity_type = "Bacteria"
                                bacteria_FN += 1
                                FN.write(entity_type + "\t" + str(an_start) + "\t" + str(an_end) + "\t" + an_name.encode('utf8') + "\n")
                            else:
                                entity_type = "Habitat"
                                habitat_FN += 1
                            idx_ann += 1


   

    FP.close()
    FN.close()
    OL.close()
    TP.close()
    NM.close()
    return [bacteria_TP, bacteria_overlap, bacteria_FN, bacteria_FP, bacteria_NM, habitat_TP, habitat_overlap, habitat_FN, habitat_FP]

def new_tagger(entities, names, stopwords):
    tagger = Tagger()
    tagger.load_names(entities, names)
    tagger.load_global(stopwords)
    return tagger

def print_eval(results):
    bacteria_TP, bacteria_overlap, bacteria_FN, bacteria_FP, bacteria_NM, habitat_TP, habitat_overlap, habitat_FN, habitat_FP = results

    print "Bacteria eval"
    print "\tTP: " + str(bacteria_TP)
    print "\toverlap: " + str(bacteria_overlap)
    print "\tnormalization: " + str(bacteria_NM)
    print "\tFN: " + str(bacteria_FN)
    print "\tFP: " + str(bacteria_FP)

    bacteria_FN += bacteria_NM
    bacteria_FP += bacteria_NM

    print "\toverlap precision: " + str((bacteria_TP + bacteria_overlap) / float(bacteria_TP + bacteria_overlap + bacteria_FP))
    print "\toverlap sensitivity: " + str((bacteria_TP + bacteria_overlap) / float(bacteria_TP + bacteria_overlap + bacteria_FN))

    print "\tprecision: " + str((bacteria_TP) / float(bacteria_TP + bacteria_overlap + bacteria_FP))
    print "\tsensitivity: " + str((bacteria_TP) / float(bacteria_TP + bacteria_overlap + bacteria_FN))

    include_habitat = False
    if include_habitat:
        print "Habitat eval"
        print "\tTP: " + str(habitat_TP)
        print "\toverlap: " + str(habitat_overlap)
        print "\tFN: " + str(habitat_FN)
        print "\tFP: " + str(habitat_FP)
        print "\toverlap precision: " + str((habitat_TP + habitat_overlap) / float(habitat_TP + habitat_overlap + habitat_FP))
        print "\toverlap sensitivity: " + str((habitat_TP + habitat_overlap) / float(habitat_TP + habitat_overlap + habitat_FN))

        print "\tprecision: " + str((habitat_TP) / float(habitat_TP + habitat_overlap + habitat_FP))
        print "\tsensitivity: " + str((habitat_TP) / float(habitat_TP + habitat_overlap + habitat_FN))

def parse_groups(inputfile):
    groups = {} 
    with open(inputfile, 'r') as f:
        for line in f:
            member, group = line.rstrip("\n").split("\t")
            if member in groups:
                groups[member].append(group)
            else:
                groups[member] = [group]
    f.close()
    return groups

def parse_genus(inputfile):
    genus = []
    with open(inputfile, 'r') as f:
        for line in f:
            taxid = line.rstrip("\n")
            genus.append(taxid)
    f.close()
    return set(genus)

def replace_parens(document):
    # replace all the parens and text between them with ' ' in document
    # hack. there is probably a better way to do this
    modified = list(document)
    matches = re.finditer(r'\(.*?\)', document)
    for match in matches:
        for idx in range(match.start(), match.end()):
            modified[idx] = " " 
    modified = "".join(modified)
    return modified

def find_spanned_results(u_results, u_p_results, u_document):
    spanned_results = []

    idx = 0
    idx_p = 0
    while(idx < len(u_results) and idx_p < len(u_p_results)):
        start, end, entity = u_results[idx]
        start_p, end_p, entity_p = u_p_results[idx_p]
        if start == start_p:
            if end == end_p:
                spanned_results.append((start, end, entity))
            else:
                spanned_results.append((start_p, end_p, entity_p))
                spanned_results.append((start, end, entity))
        else:
                spanned_results.append((start_p, end_p, entity_p))
                spanned_results.append((start, end, entity))
        idx += 1
        idx_p += 1

        #if start == start_p:
            #spanned_results.append((start_p, end_p, entity_p))
            #idx += 1
            #idx_p += 1
        #else:
            #spanned_results.append((start, end, entity))
            #idx += 1

    while idx < len(u_results):
        start, end, entity = u_results[idx]
        spanned_results.append((start, end, entity))
        idx += 1

    while idx_p < len(u_p_results):
        spanned_results.append(u_p_results[idx_p])
        idx_p += 1

    return spanned_results

def run_bionlp(mytagger, document, document_id, allow_overlap, groups, genus):
    entity_types = []
    results = mytagger.get_matches(string_to_bytes(document), str(document_id), entity_types, allow_overlap=allow_overlap)


    # run the tagger again with all things in brackets replaced with spaces
    parens_document = replace_parens(document)
    p_results = mytagger.get_matches(string_to_bytes(parens_document), str(document_id), entity_types, allow_overlap=allow_overlap)

    span_results = find_spanned_results(results, p_results, document) # find any additional results from spanning parens

    # tagger operates on bytes, we need to convert the results to characters
    u_span_results, u_document = convert_results(span_results, string_to_bytes(document))

    results = include_dots(u_span_results, u_document) # if the tagger returns sp without . and the next char is a . then include it
    results = resolve_normalization(results) # if the tagger returns two normalizations, pick one
    results = resolve_general_norm(results, groups, genus) # if a general term is later refered to by a specific term, normalize to the specific term only if it is on the list of taxids under genus
    expanded_results = expand_strain(results, u_document)
    expanded_results = expand_acronyms(expanded_results, u_document, mytagger)
    return expanded_results, u_document

def main():
    parser = argparse.ArgumentParser(description="BioNLP contest submission")
    # TODO arguments should be the same as the tagger
    parser.add_argument('-t', '--task',
                required=False,
                default=1,
                dest='task',
                help="task to compute")
    parser.add_argument('-f', '--file',
                required=True,
                default = [],
                nargs='+',
                dest='inputfile',
                help="list of input files to parse")
    parser.add_argument('-e', '--bacteria_entities',
                required=True,
                dest='bacteria_entities',
                help="bacteria entities list")
    parser.add_argument('-n', '--bacteria_names',
                required=True,
                dest='bacteria_names',
                help="bacteria names dictionary")
    parser.add_argument('-g', '--bacteria_global',
                required=True,
                dest='bacteria_stopwords',
                help="bacteria stopword dictionary")
    parser.add_argument('-r', '--bacteria_groups',
                required=True,
                dest='bacteria_groups',
                help="bacteria group membership definitions")
    parser.add_argument('-b', '--bacteria_genus',
                required=True,
                dest='bacteria_genus',
                help="all taxids under bacteria genera")
    parser.add_argument('-a', '--habitat_entities',
                required=False,
                dest='habitat_entities',
                help="habitat entities list")
    parser.add_argument('-o', '--habitat_names',
                required=False,
                dest='habitat_names',
                help="habitat names dictionary")
    parser.add_argument('-s', '--habitat_global',
                required=False,
                dest='habitat_stopwords',
                help="habitat stopword dictionary")
    parser.add_argument('-u', '--evaluate',
                action='store_true',
                required=False,
                default=False,
                dest='evaluate',
                help="calculate precision and sensitivity against manually tagged .a1 files")
    args=parser.parse_args()
    
    
    document_id = 1
    habitat = False

    if args.inputfile and args.bacteria_entities and args.bacteria_names and args.bacteria_stopwords:
        # start a tagger for bacteria
        bacteria_tagger = new_tagger(args.bacteria_entities, args.bacteria_names, args.bacteria_stopwords)

        if args.habitat_entities and args.habitat_names and args.habitat_stopwords:
            habitat_tagger = new_tagger(args.habitat_entities, args.habitat_names, args.habitat_stopwords)
            habitat = True

        eval_results = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        for inputfile in args.inputfile:
            document, tindex = parse_input(inputfile)

            allow_overlap = False
            bacteria_groups = parse_groups(args.bacteria_groups)
            bacteria_genus = parse_genus(args.bacteria_genus)
            bacteria_expanded_results, bacteria_u_document = run_bionlp(bacteria_tagger, document, document_id, allow_overlap, bacteria_groups, bacteria_genus)

            if habitat:
                allow_overlap = True
                habitat_expanded_results, habitat_u_document = run_bionlp(habitat_tagger, document, document_id, allow_overlap)

                if habitat_u_document != bacteria_u_document:
                    print "Warning: documents returned are not identical"

                results = merge_results(bacteria_expanded_results, habitat_expanded_results)
            else:
                results = bacteria_expanded_results

            print_results(results, bacteria_u_document, inputfile, tindex)

            document_id += 1

            if args.evaluate:
                ignore_normalization = False
                eval_results = map(add, eval_results, evaluate_results(results, inputfile, bacteria_u_document, ignore_normalization))

        if args.evaluate:
            print_eval(eval_results)

if __name__ == "__main__":
    main()
