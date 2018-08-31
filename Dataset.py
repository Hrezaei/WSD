import json
from Utility import read_file, write_file, prepare_wordnet
import sys

def find_ambiguous_examples(name):
    base_path = 'resources/' + name + '/'
    raw = read_file(base_path + 'all_synsets.json')
    dataset_synsets = json.loads(raw)
    words_path = base_path + 'examples_words.json'
    output = json.loads(read_file(words_path))
    ambigs_path = base_path + 'ambigs.json'
    ambigs = json.loads(read_file(ambigs_path))
    processed_path = base_path + 'parsed_synsets.json'
    parsed = json.loads(read_file(processed_path))
    wordnet = prepare_wordnet(name)
    i = 0
    j = len(parsed)
    for syn_id in dataset_synsets:
        j += 1
        item = dataset_synsets[syn_id]
        if syn_id in parsed or 'example' not in item:
            continue
        i += 1
        example = item['example']
        for sentence in example.split('*'):
            entry = item.copy()
            all_syns, candid_syns = wordnet.extract_synsets(sentence)
            entry['example'] = sentence
            entry['words'] = candid_syns
            #@todo: @bug: If an example contains "*", current code only keeps the last sentence
            output[syn_id] = entry
            if len(sentence) < 30:
                continue
            #If a long enough example has more than one meaning for the word that is 
            #representative of syn_id(sense_snapshot), it is a good item for wsd dataset:
            for key in candid_syns:
                if int(syn_id) in candid_syns[key] and len(candid_syns[key]) > 1:
                    entry['ambig_word'] = key
                    #@todo: @bug: If an example contains "*", current code only keeps the last sentence
                    ambigs[syn_id] = entry
                    #We found anchor word, do not iterate over other words of the example
                    break
            
        parsed.append(syn_id)
        if(i % 10) == 0:
            print("Parsed {} examples, {} ambigs found".format(j, len(ambigs)))
        if i > 200:
            break
    write_file(words_path, json.dumps(output, ensure_ascii=False))
    write_file(ambigs_path, json.dumps(ambigs, ensure_ascii=False))
    write_file(processed_path, json.dumps(parsed, ensure_ascii=False))

def find_almost_certain_examples(name):
    """ Tries to find examples in which all words have only one synsets except the main word"""
    ambigs = json.loads(read_file('resources/' + name + '/ambigs.json'))
    certain_sens = 0
    num_certains = []
    certain_examples = []
    for syn_id in ambigs:
        item = ambigs[syn_id]
        certain_words = 0
        for key in item['words']:
            if len(item['words'][key]) == 1:
                certain_words += 1
        num_certains.append(certain_words)
        if certain_words == len(item['words'])-1:
            certain_sens += 1
            certain_examples.append(item)
    import numpy as np
    import matplotlib.pyplot as plt
    print(np.histogram(num_certains))
    plt.hist(num_certains, bins=np.arange(12)-.5)
    plt.ylabel('Number of sentences')
    plt.xlabel('Number of certain words')
    plt.show()
    print(len(ambigs), certain_sens, sum(num_certains))
    write_file('resources/' + name + '/certains.json', json.dumps(certain_examples, ensure_ascii=False))

def find_gloss_relations(name):
    base_path = 'resources/' + name + '/'
    words_path = base_path + 'all_synsets.json'
    relations_path = base_path + 'gloss_relations.json'
    processed_path = base_path + 'gloss_parsed.json'
    parsed_synsets = json.loads(read_file(words_path))
    wordnet = prepare_wordnet(name)
    relations = json.loads(read_file(relations_path))
    processed_syns = json.loads(read_file(processed_path))
    i = 0
    j = len(processed_syns)
    for syn_id in parsed_synsets:
        j += 1
        if syn_id in processed_syns:
            continue
        processed_syns.append(syn_id)
        i += 1
        syn_data = parsed_synsets[syn_id]
        temp, words = wordnet.extract_synsets(syn_data['gloss'])
        for word_tag in words:
            if len(words[word_tag]) == 1:
                relations.append((syn_id, str(words[word_tag][0])))
        if i % 10 == 0:
            print('{} relations found so far(iteration:{})'.format(len(relations), j))
        if i > 150:
            break
    write_file(relations_path, json.dumps(relations))
    write_file(processed_path, json.dumps(processed_syns))
    print("{} gloss relations found and written to {} folder".format(len(relations), name))




#find_almost_certain_examples('Wordnet')
if len(sys.argv) > 1 and sys.argv[1] == 'amb':
    find_ambiguous_examples('Wordnet')
else:
    find_gloss_relations('Wordnet')
