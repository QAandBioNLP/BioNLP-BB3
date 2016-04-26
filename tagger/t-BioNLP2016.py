# -*- coding: utf-8 -*-

import unittest
import os
import sys
from BioNLP2016 import *



testcases_expansion = [
# strains should be expanded
        ["strain is included as part of the match from the tagger", 
                'the cytoplasmic membranes of Ralstonia eutropha H850 were investigated by measuring fluorescence polarization',
                ['Ralstonia eutropha H850',]
        ], 
        ["strain should be expanded 1", 
                'the streptomycin-resistant strain of Bacillus intermedius S3-19 and purified as a homogeneous preparation',
                ['Bacillus intermedius S3-19', ]
        ], 
        ["strain should not be expanded",
            'the growth potential of F. tularensis LVS strain in macrophage-like cell line J774',
            ['F. tularensis LVS',]
        ],
        ['strain should be expanded 3',
            'the nitrogen-fixing soil cyanobacterium Anabaena sp. strain L-31 exhibited significantly superior abilities',
            ['cyanobacterium', 'Anabaena sp. strain L-31']
        ],
        ["strain should be expanded 4",
            'Quorum-sensing regulation of adhesion in Serratia marcescens MG1 is surface dependent',
            ['Serratia marcescens MG1']
        ],
        ["strain should be expanded 5",
            'inclusions of the Bacillus thuringiensis serovar sotto strain 96-OK-85-24, for comparison with two well-characterized',
            ['Bacillus thuringiensis serovar sotto strain 96-OK-85-24']
        ],
        ["strain should be expanded sp",
            'inclusions of the Mycobacterium spp. comparison with two well-characterized',
            ['Mycobacterium spp.']
        ],
        ["strain should be expanded sp",
            'inclusions of the Mycobacterium spp comparison with two well-characterized',
            ['Mycobacterium spp']
        ],
        ['strain expansion colons K88', # expand these strains with full genus or abbreviation 
            'inhibit adhesion of Escherichia coli O8:K88 to intestinal mucosa. words blah E. coli O8:K88 does an important thing',
            ['Escherichia coli O8:K88', 'E. coli O8:K88']
        ], 
        ['strain expansion colons H7',
            'derivatives against the food pathogen Escherichia coli O157:H7 were investigated under extreme incubation conditions. attachment of E. coli O157:H7 to these surfaces.',
            ['Escherichia coli O157:H7', 'E. coli O157:H7']
        ], 
        ['strain expansion colons O:1',
            'Two symptom-free excretors of Vibrio cholerae O:1 were detected in household contacts of the patients. people with V. cholerae O:1 infection gave a history of recent consumption',
            ['Vibrio cholerae O:1', 'V. cholerae O:1']
        ], 
        ['no strain expansion following colons',
            'Two symptom-free excretors of Vibrio cholerae: ST54 that is not a strain in household contacts of the patients',
            ['Vibrio cholerae']
        ], 
        ["can do strain expansion around acronym",
            'the Sakai strain of enterohemorrhagic E. coli (EHEC) O157:H7 is much larger than',
            ['E. coli (EHEC) O157:H7',]
        ],
        ["can do strain expansion around acronym and more parens",
            'the Sakai strain of enterohemorrhagic E. coli (EHEC) O157:H7 is much larger than and from Shigella (OspD, OspE, OspG), and two ',
            ['E. coli (EHEC) O157:H7', 'Shigella', ]
        ],

        ["can do strain expansion around unicode in parens (just a check to make sure positions are correct)",
            'the Sakai strain of enterohemorrhagic E. coli (6.6 log₁₀ CFU/ml) O157:H7 is much larger than',
            ['E. coli (6.6 log₁₀ CFU/ml) O157:H7',]
        ],
        ["can do strain expansion inside parens",
            'the Sakai strain of enterohemorrhagic (E. coli O157:H7 foo) is much larger than also V. cholerae',
            ['E. coli O157:H7', 'V. cholerae']
        ],
        ["can do strain expansion inside parens as last item",
            'the Sakai strain of enterohemorrhagic (E. coli O157:H7) is much larger than also V. cholerae',
            ['E. coli O157:H7', 'V. cholerae']
        ],
        ['acronym after genus still finds species',
                'The ability of Lactobacillus (Lb.) gasseri K 7 to inhibit adhesion of ',
                ['Lactobacillus (Lb.) gasseri K 7']
        ],
        ["positions are correct after unicode",
            'the Sakai strain of enterohemorrhagic (6.6 log₁₀ CFU/ml) E. coli O157:H7 is much larger than',
            ['E. coli O157:H7',]
        ],
        ['punctuation following match is not included in match parens',
                'related to purple sulfur bacteria (the genera Ectothiorhodospira and Chromatium), it is not a phototrophic',
                ['purple sulfur bacteria', 'Ectothiorhodospira', 'Chromatium']
        ],
        ['PNEW punctuation following match is not included in match dash',
                'during Mycobacterium tuberculosis (Mtb) infection, the Mtb downregulated in Mtb-infected human blood',
                ['Mycobacterium tuberculosis', 'Mtb', 'Mtb', 'Mtb']
        ],
        ['punctuation following match is not included in match dash MRSA',
                'of viable methicillin-resistant Staphylococcus aureus (MRSA). isolates were MRSA. We ran finding MRSA-contaminated surfaces',
                ['Staphylococcus aureus', 'MRSA', 'MRSA', 'MRSA']
        ],
        ['species that is not followed by a word should not be tagged',
                'alkaline phosphatases from other Bacillus species in its physicochemical and catalytic',
                ['Bacillus']
        ],
        ['punctuation following species expansion is not included, and species expansion happens',
                'two years of age, while Shigella spp, and enterotoxigenic B. fragilis were mostly seen',
                ['Shigella spp', 'B. fragilis']
        ],
        ['punctuation following species expansion is included if it should be Yersinia',
                'pathogens. Yersinia spp. subvert the innate immune response',
                ['Yersinia spp.']
        ],
        ['punctuation following species expansion is not included, and strain is added to acronyms',
                'inclusions of the Bacillus thuringiensis serovar sotto strain ST96-OK-85-24, for comparison with two well-characterized mosquitocidal strains.  The strain ST96-OK-85-24 significantly differed',
                ['Bacillus thuringiensis serovar sotto strain ST96-OK-85-24', 'ST96-OK-85-24']
        ],
        ['punctuation following species expansion is not included, and strain is added to acronyms and found with punc later',
                'inclusions of the Bacillus thuringiensis serovar sotto strain ST96-OK-85-24, for comparison with two well-characterized mosquitocidal strains.  The strain ST96-OK-85-24, significantly differed',
                ['Bacillus thuringiensis serovar sotto strain ST96-OK-85-24', 'ST96-OK-85-24']
        ],
        ['punctuation following species expansion is not included, and strain is added to acronyms and found with punc later non acr match',
                'inclusions of the Bacillus thuringiensis serovar sotto strain 96-OK-85-24, for comparison with two well-characterized mosquitocidal strains.  The strain 96-OK-85-24, significantly differed',
                ['Bacillus thuringiensis serovar sotto strain 96-OK-85-24', '96-OK-85-24']
        ],

        ['dot following species expansion is included even when more punctuation follows -- tagger',
                'dominated by a Vibrio sp., resembling',
                ['Vibrio sp.']
        ],
        ['dot following species expansion is included even when more punctuation follows -- strain expansion',
                'blah words blah L. lactis subsp. cremoris str., something or other blah',
                ['L. lactis subsp. cremoris str.']
        ],
        ['expand after type',
                'Ampicillin-resistant Haemophilus influenzae type B have been reported only',
                ['Haemophilus influenzae type B']
        ],
        ['expansion after spp is more limited',
                'the prevalence of thermotolerant Campylobacter spp. The samples were processed',
                ['Campylobacter spp.']
        ],
        ['punctuation between strain identifier and strain name gets boundaries correct',
                'from a pathogenic Pseudomonas fluorescens strain, TSS, isolated from diseased Japanese flounder',
                ['Pseudomonas fluorescens strain, TSS']
        ],
        ['punctuation between strain identifier and strain name gets boundaries correct many commas',
                'from a pathogenic Pseudomonas fluorescens strain, TSS, spp, BLAH isolated from diseased Japanese flounder',
                ['Pseudomonas fluorescens strain, TSS, spp, BLAH']
        ],

        ['strain expansion does not catch things that look like protein names',
                'from Listeria monocytogenes ActA protein interacts',
                ['Listeria monocytogenes']
        ],
        ['strain expansion does not catch things that look like operons',
                'from Listeria monocytogenes ActAB protein interacts',
                ['Listeria monocytogenes']
        ],
        ['strain expansion is case insensitive',
                'the nitrogen-fixing soil Anabaena sp. Strain L-31 exhibited significantly superior abilities',
                ['Anabaena sp. Strain L-31']
        ],


# dictionary related
        ['gram positive should not be tagged',
                'The ratios of gram positive bacteria and fungi were increased slowly, mainly as Enterococcus and',
                ['Enterococcus']
        ],

# no expansion to do
        ["no strain expansion necessary",
            'infection due to Mycobacterium kansasii in a patient with AIDS',
            ['Mycobacterium kansasii']
        ],
]

testcases_expansion_failure = [
        ["FP overzealous expansion 1", 
                'homologue of the Agrobacterium rhizogenes TR-DNA has different morphogenetic',
                ['Agrobacterium rhizogenes',]
        ],
        ["FP overzealous expansion 2",
                'the lipid A from V. fischeri ES114 LPS was isolated and characterized by multistage',
                ['V. fischeri ES114',]
        ],
        ["FP overzealous expansion 3",
                'translocation by the X. campestris pv. vesicatoria TTS system was not detectable',
                ['X. campestris pv. vesicatoria',]
        ],
        ["FP overzealous expansion 4",
                'members of the Xanthomonas avrBs3 effector family',
                ['Xanthomonas',]
        ],

        ['FN strain expansion english words Dsij',
            'Beta-agarases A and B from Zobellia galactanivorans Dsij have recently been biochemically characterized',
            ['Zobellia galactanivorans Dsij',]
        ],
        ['FN strain expansion english words Livingstone',
            'genetic characterization of the ESBL of S. enterica Livingstone revealed',
            ['S. enterica Livingstone',]
        ],

        
]

testcases_shorthand = [
        ['strain shorthand',
            'in Anabaena sp. strain L-31 the heat-shock proteins ... activity of Anabaena cells of sp. strain L-31 continuously exposed',
            ['Anabaena sp. strain L-31', 'Anabaena', 'L-31']

        ],
]

testcases_acronyms = [
# acronyms that should be expanded
        ['acronyms expand MRSA',
            'colonization with methicillin-resistant Staphylococcus aureus (MRSA) and vancomycin-resistant',
            ['Staphylococcus aureus', 'MRSA',]
        ],
        ['acronym expand NTHi',
            'Twenty-one nontypeable Haemophilus influenzae (NTHi) isolates from the throats of two healthy children',
            ['Haemophilus influenzae', 'NTHi',]
        ],
        ['acronym expand Mtb',
                'during Mycobacterium tuberculosis (Mtb) infection, the engulfment ligand annexin1 is an important mediator',
                ['Mycobacterium tuberculosis', 'Mtb',]
        ],
        ['acronym expand punctuation VRE',
                'vancomycin-resistant Enterococcus (VRE). Time to clearance of colonization has important implications',
                ['Enterococcus', 'VRE',],
        ],
        ["acronym expansion EHEC", 
            'the Sakai strain of enterohemorrhagic E. coli (EHEC) O157:H7 is much larger than EHEC as an acronym',
            ['E. coli (EHEC) O157:H7', 'EHEC',]
        ],

        ['acronym for gene not expanded',
            'the MurNAc 6P hydrolase from Escherichia coli (MurQ-EC). To identify the roles of active site residues',
            ['Escherichia coli',]
        ],

# brackets that should not be expanded
        ['non-acronym',
                'Livingstone revealed a bla(SHV-2) gene. The bla(CTX-M-10) gene in a phage-related genetic environment S. Typhimurium',
                ['S. Typhimurium',], # need to expect at least one result for test framework to work
        ],
        ['non-acronym unicode',
            'the highest reduction rate of S. Typhimurium (6.6 log₁₀ CFU/ml) and increment in phage titre',
            ['S. Typhimurium',]
        ],
        ['acronym expand only after defined',
                'something Mtb as in mountain bikes, blah blah during Mycobacterium tuberculosis (Mtb) infection, the engulfment ligand annexin1 is an important mediator',
                ['Mycobacterium tuberculosis', 'Mtb',]
        ],
        ['acronyms not following strain is not expanded',
            'pertaining to the Three Letter Acronym (TLA) blah words something Staphylococcus aureus and vancomycin-resistant TLA lampposts',
            ['Staphylococcus aureus',]
        ],
        ['acronyms expand MRSA with strain exp',
            'colonization with methicillin-resistant Staphylococcus aureus (MRSA) and vancomycin-resistant MRSA strain MOL42 words',
            ['Staphylococcus aureus', 'MRSA', 'MRSA strain MOL42']
        ],
        ['acronyms expand MRSA with strain exp punc',
            'colonization with methicillin-resistant Staphylococcus aureus (MRSA): and vancomycin-resistant MRSA strain MOL42 words',
            ['Staphylococcus aureus', 'MRSA', 'MRSA strain MOL42']
        ],
        ['acronyms expand MRSA with strain exp not when acronym as tmesis',
            'to enterohemorrhagic E. coli (EHEC) O157:H7 is much larger than in EHEC strain MOL42 words',
            ['E. coli (EHEC) O157:H7', 'EHEC strain MOL42',]
        ],
]


testcases_acronyms_failure = [
# acronyms that will not be expanded
        ['FN incorrect format acronym',
            'a pathogenic Pseudomonas fluorescens strain, TSS, isolated from diseased Japanese flounder',
            ['Pseudomonas fluorescens', 'TSS']
        ],
        ['FN incorrect format acronym 2',
            'A TSS fur null mutant, TFM, was constructed. Compared to TSS, TFM exhibits reduced growth ability',
            ['TFM', 'TFM']
        ],
        ['FN acronym in the middle',
                'The ability of Lactobacillus (Lb.) gasseri K 7 to inhibit adhesion of Escherichia',
                ['Lactobacillus', 'Lb.']
        ],

# no false positives; acronyms we expand that we shouldn't
        
]

testcases_other = [
        ['matching with quotes',
            'The infections from "Serratia" in the Hospital S. Camillo',
            ['Serratia',]
        ],
]

testcases_normalization = [
        ['Normalization to previously mentioned',
            "human pathogens, Staphylococcus aureus, captures Hb as the first step of ... limit the capacity of S. aureus to utilize",
            [['1280'], ['1280']] # this and only this because "Staphylococcus aureus" has been mentioned previously and S. aureus has two taxids in the dictionary
        ],
        ['Normalization to specific not general works with referent',
            "multiplication of a range of Chlamydia trachomatis and C. psittaci strains in cycloheximide-treated McCoy cells have been assessed.  All chlamydiae required the addition of valine to medium and the majority required leucine",
            [['813'], ['83554'], ['813', '83554']] # when extra text is present, this will pass
        ],
        ['Normalization to strain works with referent',
            "Anabaena sp. strain L-31 exhibited significantly superior abilities.  Nitrogenase activity of Anabaena cells of sp. strain L-31 continuously exposed to heat stress",
            [['29412'], ['29412']]  # when extra text is present, this will pass
        ],
        ['Normalization to correct specific strain',
            'effectors in Escherichia coli O157 and the role of several pathogenic strains of Escherichia coli exploit type III secretion to enterohemorrhagic E. coli (EHEC) O157:H7 is much larger than in E. coli is linked to a vast phage',
            [['1045010'], ['1045010'], ['83334'], ['1045010', '83334']]  
        ],
        ['No normalization of things greater than genus',
            'something Marinobacter belong to the class of Gammaproteobacteria and these motile',
            [['2742'], ['1236']],
        ],
        ['No normalization to specific if general mentioned first',
            'something Escherichia is a more general instance of E. coli and now talking about the genus Escherichia',
            [['561'], ['562'], ['561']],
        ],
        ['Normalization to specific if general not mentioned first',
            'something no genus is a more general instance of E. coli and now talking about the genus Escherichia and getting specific',
            [['562'], ['562']],
        ],
        ['Normalization to specific if general not mentioned first moar test',
            'something no genus is a more general instance of E. coli and now talking E. coli about the genus Escherichia and getting specific',
            [['562'], ['562'], ['562']],
        ],
        ['Normalization no interference',
            'something Escherichia is a more general instance of E. coli and Chlamydia now talking E. coli about Chlamydia trachomatis the genus Escherichia or Chlamydia',
            [['561'], ['562'], ['810'], ['562'], ['813'], ['561'], ['810']],
        ],
        ['Normalization no interference to specific',
            'something is a more general instance of E. coli and now talking E. coli about Chlamydia trachomatis the genus Escherichia or Chlamydia',
            [['562'], ['562'], ['813'], ['562'], ['813']],
        ],
]

testcases_normalization_failure = [
        ['Normalization to specific not general',
            "All chlamydiae required the addition of valine to medium and the majority required leucine",
            [['813']] # normalize to genus, not to specific strain because specific strain hasn't been mentioned yet
        ],
        
        ['Normalization to strain',
            "Nitrogenase activity of Anabaena cells of sp. strain L-31 continuously exposed to heat stress",
            [['29412']]  # miss the strain because "cells of" is in the middle
        ],

        ['F Normalization specific -> general should be general if talking about others in genus',
            "the streptomycin-resistant strain of Bacillus intermedius S3-19 and purified words the secreted alkaline phosphatases from other Bacillus species in its physicochemical and catalytic properties",
            [['1400'], ['1386']] # clear that this is referring to other specific types within the general class, but we can't capture this
        ],
        ['F Normalization specific -> general should be general if talking about others in genus again',
            "the Bacillus thuringiensis serovar sotto strain 96-OK-85-24 differed from the existing mosquitocidal B. thuringiensis strains in",
            [['29340'], ['1428']] # clear that this is referring to other specific types within the general class, but we can't capture this
        ],
        
        ['F Normalization specific -> general should be general if talking about genus',
            "words Arhodomonas aquaeolei gen. nov., sp. nov., isolated from words the name Arhodomonas is proposed for the new genus",
            [['2369'], ['2368']] # clear this is not about this specific species
        ],

        # mention two strains, and then focus work on only one of them; general -> both but should -> only the one (Salmonella Typhimurium)

        # also any cases where we do not detect the strain correctly (non-O1 Vibrio cholerae)

]


class TestTagger (unittest.TestCase):

    def setUp(self):
        pass

        
    def tearDown(self):
        pass

    def test_evaluate_results_FP(self):

        # results format:
        # [bacteria_TP, bacteria_overlap, bacteria_FN, bacteria_FP, bacteria_NM, habitat_TP, habitat_overlap, habitat_FN, habitat_FP]

        results = [ (75, 97, ((-2, 100),)), (214, 236, ((-2, 100),)), (449, 464, ((-2, 100),)) ]
        annotat = [ (75, 98, ((-2, 100),)), (449, 465, ((-2, 100),)) ]
        expected = [2, 0, 0, 1, 0, 0, 0, 0, 0]
        self.assertEqual(expected, evaluate_results_h(results, annotat))

    def test_evaluate_results_FN(self):
        results = [ (75, 97, ((-2, 100),)), (449, 464, ((-2, 100),)) ]
        annotat = [ (75, 98, ((-2, 100),)), (214, 235, ((-2, 100),)), (449, 465, ((-2, 100),)) ]
        expected = [2, 0, 1, 0, 0, 0, 0, 0, 0]
        self.assertEqual(expected, evaluate_results_h(results, annotat))

    def test_evaluate_results_overlap(self):
        results = [ (75, 97, ((-2, 100),)), (449, 464, ((-2, 100),)) ]
        annotat = [ (60, 80, ((-2, 100),)), (80, 200, ((-2, 100),)), (449, 465, ((-2, 100),)) ]
        expected = [1, 1, 1, 0, 0, 0, 0, 0, 0]
        self.assertEqual(expected, evaluate_results_h(results, annotat))
        
    def test_evaluate_results_boundary(self):
        results = [ (75, 97, ((-2, 100),)) ]
        annotat = [ (98, 110, ((-2, 100),)) ]
        expected = [0, 1, 0, 0, 0, 0, 0, 0, 0]
        self.assertEqual(expected, evaluate_results_h(results, annotat))

    def test_evaluate_results_boundary(self):
        results = [ (75, 96, ((-2, 100),)) ]
        annotat = [ (98, 110, ((-2, 100),)) ]
        expected = [0, 0, 1, 1, 0, 0, 0, 0, 0]
        self.assertEqual(expected, evaluate_results_h(results, annotat))
        
    def test_evaluate_results_end_r(self):
        results = [ (75, 97, ((-2, 100),)), (214, 236, ((-2, 100),)), (449, 464, ((-2, 100),)), (500, 510, ((-2, 100),)) ]
        annotat = [ (75, 98, ((-2, 100),)), (449, 465, ((-2, 100),)) ]
        expected = [2, 0, 0, 2, 0, 0, 0, 0, 0]
        self.assertEqual(expected, evaluate_results_h(results, annotat))

    def test_evaluate_results_end_a(self):
        results = [ (75, 97, ((-2, 100),)), (214, 236, ((-2, 100),)), (449, 464, ((-2, 100),)) ]
        annotat = [ (75, 98, ((-2, 100),)), (449, 465, ((-2, 100),)), (500, 510, ((-2, 100),)) ]
        expected = [2, 0, 1, 1, 0, 0, 0, 0, 0]
        self.assertEqual(expected, evaluate_results_h(results, annotat))

    def test_evaluate_results_beg_r(self):
        results = [ (1, 10, ((-2, 100),)), (75, 97, ((-2, 100),)), (449, 464, ((-2, 100),)) ]
        annotat = [ (75, 98, ((-2, 100),)), (214, 235, ((-2, 100),)), (449, 465, ((-2, 100),)) ]
        expected = [2, 0, 1, 1, 0, 0, 0, 0, 0]
        self.assertEqual(expected, evaluate_results_h(results, annotat))

    def test_evaluate_results_beg_a(self):
        results = [ (75, 97, ((-2, 100),)), (449, 464, ((-2, 100),)) ]
        annotat = [ (1, 10, ((-2, 100),)), (75, 98, ((-2, 100),)), (214, 235, ((-2, 100),)), (449, 465, ((-2, 100),)) ]
        expected = [2, 0, 2, 0, 0, 0, 0, 0, 0]
        self.assertEqual(expected, evaluate_results_h(results, annotat))

    def test_coords_overlap(self):
        self.assertEqual(True, coords_overlap(100, 200, 150, 175))
        self.assertEqual(True, coords_overlap(100, 200, 50, 150))
        self.assertEqual(True, coords_overlap(100, 200, 150, 250))
        self.assertEqual(True, coords_overlap(100, 200, 100, 200))
        self.assertEqual(True, coords_overlap(100, 200, 50, 100))
        self.assertEqual(False, coords_overlap(1,10, 100, 110))
        self.assertEqual(False, coords_overlap(1,99, 100, 110))
        self.assertEqual(True, coords_overlap(1,100, 100, 110))



class TestArray(unittest.TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass

    pass

def test_generator(document, expecteds):
    def test(self):
        document_id = 1
        expanded_results, u_document = run_bionlp(bacteria_tagger, document, document_id, bacteria_allow_overlap, groups, genus)
        all_equal = True
        print
        print "-- " + str(self)
        for result, expected in map(None, expanded_results, expecteds):
            name = 'None'
            if result:
                name = get_name(result, u_document)
                print "result " + str(result)
            print "testing r>" + str(name.encode("utf-8")) + "<"
            print "        e>" + str(expected) + "<"
            if result is None or expected is None:
                print "  ne because none"
                all_equal = False
            else:
                if is_bacteria(result):
                    if name.encode("utf-8") != expected:
                        print "  ne"
                        all_equal = False
        self.assertTrue(all_equal)

    return test

def test_generator_failure(document, expecteds):
    def test(self):
        document_id = 1
        expanded_results, u_document = run_bionlp(bacteria_tagger, document, document_id, bacteria_allow_overlap, groups, genus)
        all_equal = True # fail if any of the results don't match
        for result, expected in map(None, expanded_results, expecteds): # works in Python 2 only
            if result is None or expected is None:
                all_equal = False
            else:
                if is_bacteria(result):
                    if not get_name(result, u_document) == expected:
                        all_equal = False

        self.assertFalse(all_equal)
    return test


def test_normalization(document, expecteds):
    def test(self):
        document_id = 1
        expanded_results, u_document = run_bionlp(bacteria_tagger, document, document_id, bacteria_allow_overlap, groups, genus)
        all_equal = True
        print
        print "-- " + str(self)
        for result, expected in map(None, expanded_results, expecteds): # works in Python 2 only
            print "testing r>" + str(get_normids(result)) + "<"
            print "        e>" + str(expected) + "<"
            if is_bacteria(result):
                if get_normids(result) != expected:
                    all_equal = False
        self.assertTrue(all_equal)
    return test

def test_normalization_failure(document, expected):
    def test(self):
        document_id = 1
        expanded_results, u_document = run_bionlp(bacteria_tagger, document, document_id, bacteria_allow_overlap, groups, genus)
        all_equal = True
        for result in expanded_results:
            if is_bacteria(result):
                if not get_normids(result) == expected:
                    all_equal = False
        self.assertFalse(all_equal)
    return test

if __name__ == '__main__':
    # set up the tagger only once because it's a bit slow to load the files
    bacteria_entities = "dict/bacteria_entities.tsv"
    bacteria_names = "dict/bacteria_names.tsv"
    bacteria_stopwords = "dict/bacteria_stopwords.tsv"
    bacteria_groups = "dict/bacteria_groups.tsv"
    bacteria_genus = "dict/bacteria_genus"
    bacteria_tagger = new_tagger(bacteria_entities, bacteria_names, bacteria_stopwords)
    groups = parse_groups(bacteria_groups)
    genus = parse_genus(bacteria_genus)
    bacteria_allow_overlap = False

    # generate a test case for each test
    for t in testcases_expansion + testcases_acronyms:
        testname, document, expected = t
        test_name = 'test_%s' % "_".join(t[0].split(" "))
        test = test_generator(document, expected)
        setattr(TestArray, test_name, test)

    for t in testcases_expansion_failure + testcases_acronyms_failure:
        testname, document, expected = t
        test_name = 'test_%s' % "_".join(t[0].split(" "))
        test = test_generator_failure(document, expected)
        setattr(TestArray, test_name, test)

    for t in testcases_normalization:
        testname, document, expected = t
        test_name = 'test_%s' % "_".join(t[0].split(" "))
        test = test_normalization(document, expected)
        setattr(TestArray, test_name, test)
        
    for t in testcases_normalization_failure:
        testname, document, expected = t
        test_name = 'test_%s' % "_".join(t[0].split(" "))
        test = test_normalization_failure(document, expected)
        setattr(TestArray, test_name, test)
        

    unittest.main()

suite = unittest.TestLoader().loadTestsFromTestCase(TestTagger)
unittest.TextTestRunner(verbosity=2).run(suite)

