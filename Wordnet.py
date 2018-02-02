import nltk
from nltk.corpus import wordnet as wn
import json
from Utility import write_file, read_file
from nltk.corpus import stopwords
from Importer import importFromPaj


class Wordnet:

    name = 'Wordnet'
    tag_map = {
        'ADJ': wn.ADJ,
        'NOUN': wn.NOUN,
        'VERB': wn.VERB,
        #'NUM': wn.NUM,
        'ADV': wn.ADV
    }

    _graph = {}
    _synsets = {}
    _ambigs = {}

    def graph(self):
        if self._graph == {}:
            self._graph = importFromPaj('resources/Wordnet/hypernyms_graph.paj')
        return self._graph

    def generateDataset(self):
        dataset = {}
        for syn in list(wn.all_synsets()):
            syn_id = syn.offset()
            item = {
                'id': syn_id,
                'senses_snapshot': ','.join([str(lem.name()) for lem in syn.lemmas()]),
                'gloss': syn.definition()
            }
            if len(syn.examples()) > 0:
                item['example'] = syn.examples()[0]
            dataset[syn_id] = item

        write_file('resources/Wordnet/all_synsets.json', json.dumps(dataset))

    def fetch_synsets(self, w, tag):
        """ Loads all synset ids of given word having given pos tag.
        tag should be from Wordnet tagset"""
        if tag not in self.tag_map:
            #print(w + ' UNKNOWN TAG:' + tag)
            return []
        pos = self.tag_map[tag]
        synsets = wn.synsets(w, pos=pos)
        output = []
        for syn in synsets:
            output.append(syn.offset())
        return output

    def fetch_definition(self, syn_id):
        if self._synsets == {}:
            # fp = open('resources/Wordnet/words.json', '+w')
            # self._synsets = json.load(fp)
            self._synsets = json.loads(read_file('resources/Wordnet/all_synsets.json'))
        return self._synsets[str(syn_id)]

    def extract_synsets(self, sentence):
        words = nltk.word_tokenize(sentence)
        stop_words = set(stopwords.words('english'))
        words = [w for w in words if w not in stop_words]
        tags = nltk.pos_tag(words, tagset='universal')
        porter = nltk.PorterStemmer()
        candid_syns = {}
        all_syns = []
        for (w, tag) in tags:
            #tag = self.tag_map[tag]
            syns = self.fetch_synsets(w, tag)
            if len(syns) == 0:
                root = porter.stem(w)
                if root is not "" and root != w:
                    syns = self.fetch_synsets(root, tag)
            if len(syns) > 0:
                candid_syns[w + '_' + tag] = syns
            for s in syns:
                all_syns.append(str(s))
        return all_syns, candid_syns

    def export_paj(self):
        nodes = []
        edges = []
        for syn in list(wn.all_synsets()):
            label = ','.join([str(lem.name()) for lem in syn.lemmas()])
            syn_id = str(syn.offset())
            nodes.append(syn_id + ' "' + label + '"')
            for target in syn.hypernyms():
                edges.append(syn_id + '      ' + str(target.offset()) + '       "Hypernym"')
            for target in syn.instance_hypernyms():
                edges.append(syn_id + '      ' + str(target.offset()) + '       "InstanceHypernym"')
            for target in syn.part_meronyms():
                edges.append(syn_id + '      ' + str(target.offset()) + '       "PartMeronyms"')
            for target in syn.member_meronyms():
                edges.append(syn_id + '      ' + str(target.offset()) + '       "MemberMeronyms"')
            for target in syn.substance_meronyms():
                edges.append(syn_id + '      ' + str(target.offset()) + '       "SubstanceMeronyms"')
            for target in syn.topic_domains():
                edges.append(syn_id + '      ' + str(target.offset()) + '       "TopicDomains"')
        output = "*Vertices      9\n   "
        output += "\n   ".join(nodes)
        output += "\n*Arcs\n   "
        output += "\n   ".join(edges)
        write_file('resources/Wordnet/hypernyms_graph.paj', output)

    def find_ambig_by_id(self, syn_id):
        if self._ambigs == {}:
            # fp = open('resources/Wordnet/words.json', '+w')
            # self._synsets = json.load(fp)
            self._ambigs = json.loads(read_file('resources/Wordnet/ambigs.json'))
        return self._ambigs[int(syn_id)]

#s = Wordnet()
#s.generateDataset()
#s.export_paj()