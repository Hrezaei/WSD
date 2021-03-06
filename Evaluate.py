
from Utility import read_file, write_file, prepare_wordnet
import json
from DoWSD import run_wsd
import numpy as np
import sys

if len(sys.argv) == 0:
    print('Please specify dataset')
    exit(4)

dataset = sys.argv[1]

wordnet = prepare_wordnet(dataset)

test_set_size = 100
#ambs = json.loads(read_file('resources/' + dataset + '/ambigs.json'))
#ambs = json.loads(read_file('resources/certains.json'))
#test_set_keys = np.random.choice(list(ambs.keys()), test_set_size, False)
#test_set = []
#for key in test_set_keys:
#    test_set.append(ambs[key])
#test_set = ambs[:test_set_size]

#write_file('debug/' + dataset + '/last_test_set.json', json.dumps(list(test_set), ensure_ascii=False))
test_set = json.loads(read_file('debug/' + dataset + '/last_test_set.json'))

total_true = 0
i = 0
baseline = 0
fatals = 0
isolated_syns = 0
zero_edges = {'positive': 0, 'negative': 0}
sum_edges = 0
sum_nodes = 0
for item in test_set:
    i += 1
    all_syns = [str(j) for k in item['words'] for j in item['words'][k]]
    answer, report = run_wsd((all_syns, item['words']), wordnet, True)
    ranks = report['ranks']
    ambig_key = item['ambig_word']
    baseline += 1/len(item['words'][ambig_key])

    if ambig_key not in answer:
        is_all_zero = True
        for k in ranks[ambig_key]:
            if k['rank'] != 0:
                is_all_zero = False
        if is_all_zero:
            isolated_syns += 1
        print("Fatal ERROR: ambig key {} is not in answer".format(ambig_key), item, answer)
        fatals += 1
        continue
    success = item['id'] == answer[item['ambig_word']]
    if success:
        total_true += 1
        print("{}/{} id:{} OK".format(total_true, i, item['id']))
    else:
        print("{}/{} on:{} id:{}  :(".format(total_true, i, item['ambig_word'], item['id']), item['example'])

    sum_edges += report['edges']
    sum_nodes += report['nodes']
    if report['edges'] == 0:
        if success:
            zero_edges['positive'] += 1
        else:
            zero_edges['negative'] += 1

print("Precision:{}  Random baseline:{} isolated:{} ".format(total_true/test_set_size, baseline/test_set_size,
                                                                      isolated_syns))
print("zero edges:", zero_edges)
print("avg nodes:{} avg edges:{}".format(sum_nodes/test_set_size, sum_edges/test_set_size))
