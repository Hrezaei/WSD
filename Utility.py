from hazm import POSTagger, Normalizer, Stemmer

tagger = POSTagger(model='resources/postagger.model')
normalizer = Normalizer()
stemmer = Stemmer()


def read_file(path):
    """Reads content of the file in path"""
    file = open(path, "r")
    return file.read()


def write_file(path, content, append=False):
    """Writes content to the file in path"""
    f_file = open(path, '+w')
    f_file.writelines(content)
    f_file.close()


def prepare_wordnet(name=None, lang=None):
    if name == 'Farsnet' or lang == 'fa':
        from Farsnet import Farsnet
        wordnet = Farsnet()
    elif name == 'Wordnet' or lang == 'en':
        from Wordnet import Wordnet
        wordnet = Wordnet()
    else:
        print('Dataset/Language "{}"/"{}" not found!'.format(name, lang))
        exit(5)
    return wordnet

