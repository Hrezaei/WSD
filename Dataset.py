import json
from Utility import read_file, write_file, prepare_wordnet


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
    for syn_id in dataset_synsets:
        item = dataset_synsets[syn_id]
        if syn_id in parsed or 'example' not in item:
            continue
        i += 1
        example = item['example']
        for sentence in example.split('*'):
            if len(sentence) < 30:
                continue
            entry = item.copy()
            all_syns, candid_syns = wordnet.extract_synsets(sentence)
            entry['example'] = sentence
            entry['words'] = candid_syns
            for key in candid_syns:
                if int(syn_id) in candid_syns[key] and len(candid_syns[key]) > 1:
                    entry['ambig_word'] = key
                    ambigs[syn_id] = entry
            output[syn_id] = entry
        parsed.append(syn_id)
        if(i % 10) == 0:
            print("Parsed {} examples, {} ambigs found".format(i, len(ambigs)))
        if i > 2000:
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






#find_almost_certain_examples('Wordnet')
find_ambiguous_examples('Farsnet')

