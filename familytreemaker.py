#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Adrien Vergé

"""familytreemaker

This program creates family tree graphs from simple text files.

The input file format is very simple, you describe persons of your family line
by line, children just have to follow parents in the file. Persons can be
repeated as long as they keep the same name or id. An example is given in the
file LouisXIVfamily.txt.

This script outputs a graph descriptor in DOT format. To make the image
containing the graph, you will need a graph drawer such as GraphViz.

For instance:

$ ./familytreemaker.py -a 'Louis XIV' LouisXIVfamily.txt | \
    dot -Tpng -o LouisXIVfamily.png

will generate the tree from the infos in LouisXIVfamily.txt, starting from
Louis XIV and saving the image in LouisXIVfamily.png.

"""

__author__ = "Adrien Vergé"
__copyright__ = "Copyright 2013, Adrien Vergé"
__license__ = "GPL"
__version__ = "1.0"

import argparse
import random
import re
import sys
import json

class Person:
    """This class represents a person.

    Characteristics:
    - name            real name of the person
    - id            unique ID to be distinguished in a dictionnary
    - attr            attributes (e.g. gender, birth date...)
    - households    list of households this person belongs to
    - follow_kids    boolean to tell the algorithm to display this person's
                    descendent or not

    """

    def __init__(self, desc):
        self.attr = {}
        self.parents = []
        self.households = []

        self.name = ''
        self.id = ''

        desc = desc.strip()
        if '(' in desc and ')' in desc:
            self.name, attr = desc[0:-1].split('(')
            self.name = self.name.strip()
            attr = map(lambda x: x.strip(), attr.split(','))
            for a in attr:
                if '=' in a:
                    k, v = a.split('=')
                    self.attr[k] = v
                else:
                    self.attr[a] = True
        else:
            self.name = desc

        if 'id' in self.attr:
              self.id = self.attr['id']
        else:
            self.id = re.sub('[^0-9A-Za-z]', '', self.name)
            if 'unique' in self.attr:
                  self.id += str(random.randint(100, 999))

        self.follow_kids = True

    @classmethod
    def from_json(self, json_object):

        ID_KEY = 'id'
        NAME_KEY = 'name'

        person = Person('')

        for key in json_object.keys():
            if key == ID_KEY:
                person.id = json_object[ID_KEY]
            elif key == NAME_KEY:
                person.name = json_object[NAME_KEY]
            else:
                person.attr[key] = json_object[key]

        return person

    def to_json(self):

        attr_list = []
        for attr_key in self.attr.keys():
            if self.attr[attr_key] == True:
                attr_list.append(f'"sex":"{attr_key}"')
            elif attr_key not in ["id"]:
                attr_list.append(f'"{attr_key}":"{self.attr[attr_key]}"')

        attr_string = ""
        if len(attr_list) > 0:
            attr_string = f',{",".join(attr_list)}'

        json_string = "{" + f'"id": "{self.id}", "name":"{self.name}"{attr_string}' + "}"

        return json_string


    def __str__(self):
        return self.name

    def dump(self):
        return    'Person: %s (%s)\n' % (self.name, str(self.attr)) + \
                '  %d households' % len(self.households)

    def graphviz(self):
        label = self.name
        if 'pretitle' in self.attr:
            label = self.attr['pretitle'] + ' ' + label
        if 'posttitle' in self.attr:
            label += ' ' + self.attr['posttitle']
        if 'surname' in self.attr:
            label += '\\n« ' + str(self.attr['surname']) + '»'        
        if 'nee' in self.attr: # Nee = maiden's name (Geb. in german)
            label += '\\nGeb. ' + str(self.attr['nee'])
        if 'birthday' in self.attr:
            label += '\\n* ' + str(self.attr['birthday'])
            if 'birthplace' in self.attr:
                label += ' in ' + str(self.attr['birthplace'])
        elif 'birthplace' in self.attr:
            label += '\\n* in ' + str(self.attr['birthplace'])
        if 'deathday' in self.attr:
            label += '\\n† ' + str(self.attr['deathday'])
            if 'deathplace' in self.attr:
                label += ' in ' + str(self.attr['deathplace'])
        elif 'deathplace' in self.attr:
            label += '\\n† in ' + str(self.attr['deathplace'])
        if 'notes' in self.attr:
            label += '\\n' + str(self.attr['notes'])

        opts = ['label="' + label + '"']
        opts.append('style=filled')
        if 'sex' in self.attr:
            color = 'white'
            if self.attr['sex'] == 'F':
                color = 'bisque'
            elif self.attr['sex'] == 'M':
                color = 'azure2'
            opts.append(f'fillcolor={color}')
        else:
            opts.append('fillcolor=' + ('F' in self.attr and 'bisque' or
                        ('M' in self.attr and 'azure2' or 'white')))
        return self.id + '[' + ','.join(opts) + ']'

class Household:
    """This class represents a household, i.e. a union of two person.

    Those two persons are listed in 'parents'. If they have children, they are
    listed in 'kids'.

    """

    def __init__(self):
        self.parents = []
        self.kids = []
        self.id = 0

        self.attr = {}
    
    def __str__(self):
        return    'Family:\n' + \
                '    parents  = ' + ', '.join(map(str, self.parents)) + '\n' \
                '    children = ' + ', '.join(map(str, self.kids))

    def isempty(self):
        if len(self.parents) == 0 and len(self.kids) == 0:
            return True
        return False

    def to_json(self):

        parents_strings = []
        index = 0
        for parent in self.parents:
            parents_strings.append(f'"ID{index}":"{parent.id}"')
            index += 1

        children_strings = []
        index = 0
        for child in self.kids:
            children_strings.append(f'"ID{index}":"{child.id}"')
            index += 1

        json_attrs = []
        for attr_key in self.attr:
            json_strings.append(f'"{attr_key}":"{self.attr[attr_key]}"')

        json_attr_string = ""
        if len(json_attrs) > 0:
            json_attr_string = "," + ",".join(json_attrs)

        json_string = "{" +\
            f'"parents":' + '{' + f'{",".join(parents_strings)}' + '},' +\
            f'"children":' + '{' + f'{",".join(children_strings)}' + '}' +\
            json_attr_string + "}"
        return json_string

class Family:
    """Represents the whole family.

    'everybody' contains all persons, indexed by their unique id
    'households' is the list of all unions (with or without children)

    """

    invisible = '[shape=circle,label="",height=0.11,width=0.11]'

    def __init__(self):
        self.everybody = {}
        self.households = []

        self.INDIVIDUALS_KEY = 'individuals'
        self.HOUSEHOLDS_KEY = 'households'


    def add_person(self, string):
        """Adds a person to self.everybody, or update his/her info if this
        person already exists.

        """
        p = Person(string)
        key = p.id

        if key in self.everybody:
            self.everybody[key].attr.update(p.attr)
        else:
            self.everybody[key] = p

        return self.everybody[key]

    def add_household(self, h):
        """Adds a union (household) to self.households, and updates the
        family members infos about this union.

        """
        if len(h.parents) != 2:
            print('error: number of parents != 2')
            return

        h.id = len(self.households)
        self.households.append(h)

        for p in h.parents:
            if not h in p.households:
                p.households.append(h)

    def find_person(self, name):
        """Tries to find a person matching the 'name' argument.

        """
        if "," in name:
            names = name.split(",")
        else:
            names = [name]
        
        persons = []
        for name in names:
            # First, search in ids
            if name in self.everybody:
                persons.append(self.everybody[name])
            # Ancestor not found in 'id', maybe it's in the 'name' field?
            for p in self.everybody.values():
                if p.name == name:
                    persons.append(p)

        if len(persons) > 0:
            return persons
        else:
            return None

    def populate_json(self, f):
        PARENTS_KEY = "parents"
        CHILDREN_KEY = "children"

        data = json.load(f)

        if self.INDIVIDUALS_KEY not in data or self.HOUSEHOLDS_KEY not in data:
            raise Exception('Input json data not supported,'+
                'check that keys "individuals" and "households" are present!')

        for individual in data[self.INDIVIDUALS_KEY]:
            p = Person.from_json(individual)

            if p.id not in self.everybody:
                self.everybody[p.id] = p

        for household in data[self.HOUSEHOLDS_KEY]:
            parents = list(household[PARENTS_KEY].values())
            children = list(household[CHILDREN_KEY].values())

            household = Household()



            for parent_key in parents:
                parent = self.everybody[parent_key]
                household.parents.append(parent)

            for child_key in children:
                child = self.everybody[child_key]
                child.parents = household.parents
                household.kids.append(child)

            self.add_household(household)

    def populate(self, f):
        """Reads the input file line by line, to find persons and unions.

        """
        h = Household()
        while True:
            line = f.readline()
            if line == '': # end of file
                if not h.isempty():
                    self.add_household(h)
                break
            line = line.rstrip()
            if line == '':
                if not h.isempty():
                    self.add_household(h)
                h = Household()
            elif line[0] == '#':
                continue
            else:
                if line.startswith("    "):
                    p = self.add_person(line[1:])
                    p.parents = h.parents
                    h.kids.append(p)
                else:
                    p = self.add_person(line)
                    h.parents.append(p)

    def find_first_ancestor(self):
        """Returns the first ancestor found.

        A person is considered an ancestor if he/she has no parents.

        This function is not very good, because we can have many persons with
        no parents, it will always return the first found. A better practice
        would be to return the one with the highest number of descendant.
        
        """
        for p in self.everybody.values():
            if len(p.parents) == 0:
                return p

    def previous_generation(self, gen):
        """Takes the generation N in argument, returns the generation N+1.

        Generations are represented as a list of persons.

        """
        prev_gen = {}

        for p in gen:
            if not p.follow_kids:
                continue
            for h in p.households:
                for p_temp in h.parents:
                    for parent in p_temp.parents:
                        if parent not in prev_gen:
                            prev_gen[parent] = parent
                            # add mother/father

        #prev_gen = list(set(prev_gen))
        return list(prev_gen.values())


    def next_generation(self, gen):
        """Takes the generation N in argument, returns the generation N+1.

        Generations are represented as a list of persons.

        """
        next_gen = []

        for p in gen:
            if not p.follow_kids:
                continue
            for h in p.households:
                next_gen.extend(h.kids)
                # append mari/femme

        return next_gen

    def get_spouse(household, person):
        """Returns the spouse or husband of a person in a union.

        """
        return    household.parents[0] == person \
                and household.parents[1] or household.parents[0]

    def display_generation(self, gen, people_printed = {}):
        """Outputs an entire generation in DOT format.

        """
        # Display persons
        print('\t{ rank=same;')

        generation_already_printed = {}

        prev = None
        for p in gen:

            l = len(p.households)

            if prev:
                if l <= 1:
                    print('\t\t%s -> %s [style=invis];' % (prev, p.id))
                else:
                    print('\t\t%s -> %s [style=invis];'
                          % (prev, Family.get_spouse(p.households[0], p).id))

            if l == 0:
                prev = p.id
                continue
            elif len(p.households) > 2:
                raise Exception('Person "' + p.name + '" has more than 2 ' +
                                'spouses/husbands: drawing this is not ' +
                                'implemented')

            # Display those on the left (if any)
            for i in range(0, int(l/2)):
                h = p.households[i]
                spouse = Family.get_spouse(h, p)
                if spouse.id not in people_printed:
                    people_printed[spouse.id] = spouse
                print('\t\t%s -> h%d -> %s;' % (spouse.id, h.id, p.id))
                print('\t\th%d%s;' % (h.id, Family.invisible))

            # Display those on the right (at least one)
            for i in range(int(l/2), l):
                h = p.households[i]
                spouse = Family.get_spouse(h, p)
                if spouse.id not in people_printed:
                    people_printed[spouse.id] = spouse
                print('\t\t%s -> h%d -> %s;' % (p.id, h.id, spouse.id))
                print('\t\th%d%s;' % (h.id, Family.invisible))
                prev = spouse.id
        print('\t}')

        # Display lines below households
        print('\t{ rank=same;')
        prev = None
        for p in gen:
            for h in p.households:

                if len(h.kids) == 0:
                    continue
                if prev:
                    print('\t\t%s -> h%d_0 [style=invis];' % (prev, h.id))
                l = len(h.kids)
                if l % 2 == 0:
                    # We need to add a node to keep symmetry
                    l += 1
                print('\t\t' + ' -> '.join(map(lambda x: 'h%d_%d' % (h.id, x), range(l))) + ';')
                for i in range(l):
                    print('\t\th%d_%d%s;' % (h.id, i, Family.invisible))
                    prev = 'h%d_%d' % (h.id, i)
        print('\t}')

        for p in gen:
            for h in p.households:

                if len(h.kids) > 0:
                    print('\t\th%d -> h%d_%d;'
                          % (h.id, h.id, int(len(h.kids)/2)))
                    i = 0
                    for c in h.kids:
                        if c.id not in people_printed:
                            people_printed[c.id] = c
                        print('\t\th%d_%d -> %s;'
                              % (h.id, i, c.id))
                        i += 1
                        if i == len(h.kids)/2:
                            i += 1

    def output_nodes(self, people_printed = {}):

        if len(list(people_printed.keys())) == 0:
            people_printed = self.everybody
        for p in people_printed.values():
            print('\t' + p.graphviz() + ';')
        print('')

    def output_ascending_tree(self, ancestor, people_printed = {}):
        """Outputs the whole descending family tree from a given ancestor,
        in DOT format.

        """

        # Find the first households
        gen = ancestor

        new_gen = []
        for person in gen:
            if person.id not in people_printed:
                people_printed[person.id] = person

            new_gen += person.parents

        gen = new_gen

        while gen:

            single_household_generation = []
            for person in gen:
                if person.id not in people_printed:
                    people_printed[person.id] = person

                if person in single_household_generation:
                    continue
            
                person_in_household_in_list = False
                for household in person.households:
                    for household_person in household.parents:
                        if household_person in single_household_generation:
                            person_in_household_in_list = True
                            break
                            
                if person_in_household_in_list is False:
                    single_household_generation.append(person)

            self.display_generation(single_household_generation, people_printed=people_printed)

            gen = self.previous_generation(gen)

        return people_printed


    def output_descending_tree(self, ancestor, people_printed = {}):
        """Outputs the whole descending family tree from a given ancestor,
        in DOT format.

        """
        # Find the first households
        gen = [ancestor[0]]

        descending_printed = {}
        
        while gen:
            for person in gen:
                if person.id not in people_printed:
                    people_printed[person.id] = person

            self.display_generation(gen, people_printed= people_printed)
            gen = self.next_generation(gen)

        return people_printed

def convert_to_json(family):
    """
    Convert family to json:
    """

    json_persons = []
    for person in family.everybody.values():
        json_persons.append(person.to_json())

    json_households = []
    for household in family.households:
        json_households.append(household.to_json())
    
    json_string = '{\n "individuals": [\n' + ",\n".join(json_persons) + '\n],\n "households": [\n' + ",\n".join(json_households) + '\n]\n}' 

    return json_string

def main():
    """Entry point of the program when called as a script.

    """
    # Parse command line options
    parser = argparse.ArgumentParser(description=
             'Generates a family tree graph from a simple text file')
    parser.add_argument('-a', '--ancestor', dest='ancestor',
                        help='make the family tree from an ancestor (if '+
                        'omitted, the program will try to find an ancestor)')
    parser.add_argument('--format', default='json', choices=['json','old'],
        dest='format', help='Specify the format')
    parser.add_argument('-c', dest='convert', action='store_true', help='Provided --format=old, then with -c '+
                        'you can convert the old format to json format (old format formatted with 4-spaces, not tabs).')
    parser.add_argument('input', metavar='INPUTFILE',
                        help='the formatted text file representing the family')
    parser.add_argument('--tree-type', dest="tree_type",
        default='family-ancestor', choices=['family','ancestor','family-ancestor'],
        help='Specify the tree type, you can choose between family tree (all descendents of one person),'+ 
                        'ancestor (all ancestors of one person, specify "-a <PERSON>" explicitly), family-ancestor (both, family and ancestor tree, specify "-a <PERSON>")')
    args = parser.parse_args()

    # Create the family
    family = Family()

    # Populate the family
    f = open(args.input, 'r', encoding='utf-8')
    if args.format == 'json':
        family.populate_json(f)
    else:
        family.populate(f)
    f.close()

    if args.convert is True:
        json = convert_to_json(family) 
        print(json)
        quit(0)

    # Find the ancestor from whom the tree is built
    if args.ancestor:
        ancestor = family.find_person(args.ancestor)
        if not ancestor:
            raise Exception('Cannot find person "' + args.ancestor + '"')
    else:
        ancestor = [family.find_first_ancestor()]

    # Output the graph descriptor, in DOT format
    print('digraph {\n' + \
            '    nodesep=0.5; ranksep=1.5;'
            '    node [shape=note];\n' + \
            '    edge [dir=none];\n')
    
    people_printed = {}
    if args.tree_type in ['ancestor', 'family-ancestor']:
        family.output_ascending_tree(ancestor, people_printed=people_printed)
    if args.tree_type in ['family', 'family-ancestor']:
        family.output_descending_tree(ancestor, people_printed=people_printed)

    family.output_nodes(people_printed=people_printed)

    print('}')

if __name__ == '__main__':
    main()
