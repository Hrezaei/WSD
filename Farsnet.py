import MySQLdb
import re
from Importer import importFromPaj
import json
from Utility import tagger, normalizer, stemmer, read_file
from Preprocess import remove_stop_words
from hazm import *


class Farsnet:
    name = 'Farsnet'
    port = 6060
    host = 'localhost'

    db = MySQLdb.connect(host="localhost",  # your host
                         user="root",       # username
                         passwd="12345",     # password
                         db="farsnet")
    db.set_character_set('utf8')
    cur = db.cursor()

    cur.execute('SET NAMES utf8;')
    cur.execute('SET CHARACTER SET utf8;')
    cur.execute('SET character_set_connection=utf8;')

    # Tagset of Hazm is not the same as tagset of FarsNet
    tag_map = {
        'AJ': 'Adjective',
        'AJe': 'Adjective',
        'N': 'Noun',
        'Ne': 'Noun',
        'V': 'Verb',
        'ADV': 'Adverb',
        'ADVe': 'Adverb'
    }

    _graph = {}
    _ambigs = None

    def graph(self):
        if self._graph == {}:
            self._graph = importFromPaj("resources/Farsnet/synset_relation.paj")
            #self._graph = importFromPaj("resources/Farsnet/synset_related_to.paj")
            #self._graph = importFromPaj("resources/Farsnet/synset_hypernyms.paj")
        return self._graph

    def extract_synsets(self, sentence):
        sentence = normalizer.normalize(sentence)
        sentence = re.sub(r'[^\w\s\u200c]', '', sentence)
        words = word_tokenize(sentence)
        words = remove_stop_words(words)
        tags = tagger.tag(words)
        candid_syns = {}
        all_syns = []
        for (w, tag) in tags:
            syns = self.fetch_synsets(w, tag)
            if len(syns) == 0:
                root = stemmer.stem(w)
                if root is not "" and root != w:
                    syns = self.fetch_synsets(root, tag)
            if len(syns) > 0:
                candid_syns[w + '_' + tag] = syns
            for s in syns:
                all_syns.append(str(s))
        return all_syns, candid_syns

    def fetch_synsets(self, w, tag):
        """ Loads all synset ids of given word having given pos tag.
        tag should be from Hazm tagset"""
        if tag in ['PUNC', 'CONJe', 'RESe', 'DETe', 'Pe', 'DET', 'NUM', 'CL', 'P', 'NUMe', 'RES', 'CONJ', 'PRO', 'POSTP', 'INT']:
            return []
        #if tag not in tag_map:
        #    return []
        pos = self.tag_map[tag]
        w = re.sub(r'[ی]', 'ي', w)
        query = "SELECT id FROM synset WHERE pos=\"" + pos + "\" and id IN (SELECT synset FROM  sense WHERE  value LIKE  \"" + w + "\")"
        self.cur.execute(query)

        output = []
        for row in self.cur.fetchall():
            output.append(row[0])
        return output

    def fetch_definition(self, syn):
        if isinstance(syn, list):
            ids = ",".join(syn)
        else:
            ids = syn
        query = "SELECT id, senses_snapshot, gloss FROM synset WHERE id in (" + ids + ")"
        self.cur.execute(query)

        output = []
        for row in self.cur.fetchall():
            output.append({'id': row[0], 'gloss': row[2], 'senses_snapshot': row[1]})
        if isinstance(syn, list):
            return output
        else:
            return output[0]

    #v=fetch_synsets('دفتر', 'N')
    #print(v)

    def find_ambig_by_id(self, syn_id):
        if self._ambigs is None:
            self._ambigs = json.loads(read_file('resources/Farsnet/examples_words.json'))
        return self._ambigs[syn_id]

    def AccuFetchSynset(self, w, tag):
        import json, os
        filePath = "Resource//synsets.json"
        if not os.path.isfile(filePath):
            file = open(filePath, "a", encoding="utf-8")
            newEntry = self.fetch_synsets(w, tag)
            file.write(json.dumps({w+"_"+tag:newEntry},ensure_ascii=False))
            file.close()
            return newEntry
        data = json.loads(open(filePath, encoding="utf-8").read())
        try:
            return data[w+"_"+tag]
        except:
            newEntry = self.fetch_synsets(w, tag)
            data[w+"_"+tag] = newEntry
            open(filePath,'w',encoding="utf-8").writelines(json.dumps(data,ensure_ascii=False))
            return newEntry




    def FetchSynsetServer(self):
        """
        IMPORTANT : should kill the server via FetchServerKill() when you're done
        :return:
        """
        import socket,json,os
        filePath = "Resource//synsets.json"
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(5)
        if not os.path.isfile(filePath):
            file = open(filePath, "a", encoding="utf-8").close()
        else:
            data = json.loads(open(filePath, encoding="utf-8").read())
        while 1:
            conn, addr = s.accept()
            request = conn.recv(4096).decode('utf-8')
            #print("Server[request]: " + request)
            if request == "exit_":
                open(filePath, 'w', encoding="utf-8").writelines(json.dumps(data,ensure_ascii=False))
                break
            w,tag = request.split("_")
            try:
                conn.sendall(str(data[w+"_"+tag]).encode('utf-8'))
                #print("Server[reply]: " + str(data[w+"_"+tag]))
            except:
                newEntry = self.fetch_synsets(w,tag)
                data[w+"_"+tag] = newEntry
                conn.sendall(str(data[w+"_"+tag]).encode('utf-8'))
                #print("Server[reply]: " + str(data[w+"_"+tag]))


    def FetchSynsetClient(self, w, tag):
        import socket
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(str(w+"_"+tag).encode('utf-8'))
        if w == "exit":
            return
        #print("Client[sent]: " + str(w+"_"+tag))
        result = s.recv(4096).decode("utf-8")
        #print("Client[result]: " + result)

    def FetchServerKill(self):
        self.FetchSynsetClient("exit", "")