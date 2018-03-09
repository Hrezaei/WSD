

from Navigli import buildGraph, buildGraphBasedOnShortest
from Utility import write_file, prepare_wordnet
import re
import sys
import json
import networkx as nx
from networkx import algorithms
from networkx.algorithms.link_analysis import hits_alg




def run_wsd(sentence, wordnet, verbose=False, exportName=False):
    if isinstance(sentence, str):
        all_syns, candid_syns = wordnet.extract_synsets(sentence)
    elif isinstance(sentence, tuple):
        (all_syns, candid_syns) = sentence
    teleport_set = {}
    for k in candid_syns:
        if len(candid_syns[k]) == 1:
            teleport_set[candid_syns[k][0]] = 10

    L = 3
    g = buildGraph(all_syns, wordnet.graph(), L)
    #g = buildGraphBasedOnShortest(candid_syns, wordnet, all_syns)

    if exportName != False:
        nx.write_gexf(g, 'export/' + wordnet.name + '/' + str(exportName) + '.gexf')
    if verbose:
        print("nodes:{} edges:{} teleport:{}".format(len(g.nodes()), len(g.edges()), len(teleport_set)))

    #ranks_deg = nx.degree_centrality(g)

    ranks_pr = nx.pagerank(g)
    if len(teleport_set) > 0:
        ranks_pr = nx.pagerank(g, personalization=teleport_set)
#    try:
#        flow_ranks = nx.approximate_current_flow_betweenness_centrality(g)    
#    except :
#        pass
    #hits = {}
    #try:
    #    hits = hits_alg.hits(g, max_iter=1000)[0]
    #except nx.exception.PowerIterationFailedConvergence:
    #    pass
    #ranks_btw = nx.betweenness_centrality(g)
    #rank_lrc = nx.communicability_betweenness_centrality(g)
    ranks = ranks_pr
    #ranks = {k: (ranks_deg.get(k, 0) + ranks_pr.get(k, 0)) for k in all_syns}
    elected = {}
    ranks_report = {}
    for key in candid_syns:
        max_rank = 0
        ranks_report[key] = []
        for syn in candid_syns[key]:
            syn_id = str(syn)
            if syn_id not in ranks:
                continue
            rank = ranks[syn_id]
            if verbose:
                definition = wordnet.fetch_definition(syn_id)
                definition['rank'] = rank
                ranks_report[key].append(definition)
            if rank > max_rank:
                max_rank = rank
                elected[key] = syn
    if verbose:
        output = {
            'teleport_size': len(teleport_set),
            'ranks': ranks_report,
            'nodes': len(g.nodes()),
            'edges': len(g.edges())
        }
        return elected, output
    return elected




electeds = []
candids = []
if len(sys.argv) > 2:
    command = sys.argv[1]
    if command == 'sen':
        from langdetect import detect
        input_sentence = sys.argv[2]
        lang = detect(input_sentence)
        wordnet = prepare_wordnet(lang=lang)
        electeds, report = run_wsd(input_sentence, wordnet, True, 'last_debug')
        print(electeds)
        #print(report)
        write_file('/tmp/last_sen.json',
                   json.dumps((input_sentence, electeds, report), ensure_ascii=False, indent=4))
        from subprocess import call
        call(["code", '/tmp/last_sen.json'])
    elif sys.argv[1] == 'debug':
        syn_id = sys.argv[2]
        dataset_name = sys.argv[3]
        wordnet = prepare_wordnet(dataset_name)
        item = wordnet.find_ambig_by_id(syn_id)
        if item is not None:
            all_syns = [str(j) for k in item['words'] for j in item['words'][k]]
            electeds, report = run_wsd((all_syns, item['words']), wordnet, True, syn_id)
            write_file('debug/' + syn_id + '.json', json.dumps((item['example'], electeds, report), ensure_ascii=False, indent=4))
            from subprocess import call
            call(["code", 'debug/' + syn_id + '.json'])
        else:
            print("synset with id {} not found".format(syn_id))

