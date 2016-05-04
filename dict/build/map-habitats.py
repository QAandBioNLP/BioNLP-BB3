import argparse

def parse_mapping(inputfile):
    obt_to_entity = {}
    with open(inputfile, 'r') as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if cols[0] in obt_to_entity:
                pass
            else:
                obt_to_entity[cols[0]] = cols[4]
    return obt_to_entity

def parse_names(inputfile):
    serial_to_names = {}
    with open(inputfile, 'r') as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if cols[0] in serial_to_names:
                serial_to_names[cols[0]].append(cols[1])
            else:
                serial_to_names[cols[0]] = [cols[1]]
    return serial_to_names

def parse_entities(inputfile):
    entity_to_serial = {}
    with open(inputfile, 'r') as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if cols[0] in entity_to_serial:
                print "this should not happen"
            else:
                entity_to_serial[cols[2]] = cols[0]
    return entity_to_serial

def parse_groups(inputfile):
    parent_to_children = {}
    child_to_parents = {}
    with open(inputfile, 'r') as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            child = cols[0]
            parent = cols[1]
            if parent in parent_to_children:
                parent_to_children[parent].append(child)
            else:
                parent_to_children[parent] = [child]
            if child in child_to_parents:
                child_to_parents[child].append(parent)
            else:
                child_to_parents[child] = [parent]
    return parent_to_children, child_to_parents


def main():
    parser = argparse.ArgumentParser(description="BioNLP contest submission")
    # TODO arguments should be the same as the tagger
    parser.add_argument('-m', '--mapping',
                required=True,
                default=1,
                dest='mapping',
                help="mapping file")
    parser.add_argument('-n', '--names',
                required=True,
                default=1,
                dest='names',
                help="names file")
    parser.add_argument('-e', '--entities',
                required=True,
                default=1,
                dest='entities',
                help="entities file")
    parser.add_argument('-g', '--groups',
                required=True,
                default=1,
                dest='groups',
                help="groups file")
    parser.add_argument('-s', '--serial',
                required=True,
                default=1,
                dest='habitat',
                help="habitat entities file")
    
    args=parser.parse_args()

    if args.mapping and args.names and args.entities and args.groups and args.habitat:
        obt_to_entity = parse_mapping(args.mapping)
        entity_to_serial = parse_entities(args.entities)
        serial_to_names = parse_names(args.names)
        parent_to_children, child_to_parents = parse_groups(args.groups)
        obt_to_habserial = parse_entities(args.habitat)

        already_mapped = []

        obt_to_names = {}

        for obt in obt_to_entity.keys():
            entity = obt_to_entity[obt]
            serial = entity_to_serial[entity]

            # get the children of this term so we can get their names
            if serial in parent_to_children:
                children = parent_to_children[serial]
            else:
                children = []


            overwrite = False # don't overwrite entries we have already added, because this would be a more general mapping overwriting a more specific (bad)
            if serial in already_mapped:
                overwrite = True # unless this is specified explicitly in the mapping file, then it is a specific overwriting a general (good)
                obt_to_names[obt] = [] # so zero it out


            for ser in children + [serial]:
                if ser in serial_to_names:
                    if overwrite:
                        names = serial_to_names[ser]
                        already_mapped.append(ser)
                        if obt in obt_to_names:
                            obt_to_names[obt] += names
                        else:
                            obt_to_names[obt] = names
                    else:
                        if ser not in already_mapped:
                            names = serial_to_names[ser]
                            already_mapped.append(ser)
                            if obt in obt_to_names:
                                obt_to_names[obt] += names
                            else:
                                obt_to_names[obt] = names


        for obt in obt_to_names:
            names = obt_to_names[obt]
            for name in names:
                if obt in obt_to_habserial:
                    print obt_to_habserial[obt] + "\t" + name
                else:
                    print "this shouldn't happen"


if __name__ == "__main__":
    main()
