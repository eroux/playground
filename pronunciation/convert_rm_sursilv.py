# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import codecs
import re
import sys


SUFFIXES = [' ' + s for s in 'I II III IV V VI VII'.split()]


PRON_OVERRIDES = {
    ' ku≈tè': 'ku≈tè',
    'geogrfè. ˆeo-': 'geogrfè',
    '(adj re≈náÕf': 're≈náÕf',
    '(pl ri√rEls': 'ri√rEls',
}


# These overrides are applied _before_ moving stress markers.
IPA_OVERRIDES = {
    'kunfˈaht': 'kunfˈaːt',
    'fɛht': 'fɛːt',
    'navntanavˈɔːs': 'navontanavˈɔːs',
    'ʃlaht': 'ʃlaːt',
    'vaht': 'vaːt',
}

# Modeled after http://universaldependencies.github.io/docs/
# TODO: [AdjType, Coll] are custom additions; they need more thought.
TAGS = {
    '(in)tr':  ['VERB|Subcat=Intr', 'VERB|Subcat=Tran'],
    'ON': ['INTJ'],
    'PN': ['PROPN'],
    'adj u. adv': ['ADJ', 'ADV'],
    'adj u. f': ['ADJ', 'NOUN|Gender=Fem'],
    'adj u. m': ['ADJ', 'NOUN|Gender=Masc'],
    'adj u. subst': ['ADJ', 'NOUN'],
    'adj': ['ADJ'],
    'adj.': ['ADJ'],
    'adj.invar': ['ADJ|AdjType=Invar'],
    'adv u. m': ['ADV', 'NOUN|Gender=Masc'],
    'adv': ['ADV'],
    'adv. u. prep': ['ADV', 'ADP'],
    'adv.': ['ADV'],
    'adv/interj': ['ADV', 'INTJ'],
    'adv; far ~': ['ADV'],
    'coll': ['NOUN|Coll=Yes'],
    'conj': ['CONJ'],
    'f  ON': ['NOUN|Gender=Fem'],
    'f  PN': ['PROPN|Gender=Fem'],
    'f u. adj': ['ADJ', 'NOUN|Gender=Fem'],
    'f u. coll': ['NOUN|Coll=Yes|Gender=Fem', 'NOUN|Gender=Fem'],
    'f u. f/coll': ['NOUN|Coll=Yes|Gender=Fem', 'NOUN|Gender=Fem'],
    'f u. m': ['NOUN|Gender=Masc', 'NOUN|Gender=Masc'],
    'f': ['NOUN|Gender=Fem'],
    'f/coll': ['NOUN|Coll=Yes|Gender=Fem'],
    'f/pl': ['NOUN|Gender=Fem|Number=Plur'],
    'inter': ['INTJ'],
    'interj': ['INTJ'],
    'intr u. refl': ['VERB|Subcat=Intr', 'VERB|Subcat=Refl'],
    'intr u. tr': ['VERB|Subcat=Intr', 'VERB|Subcat=Tran'],
    'intr': ['VERB|Subcat=Intr'],
    'intr.': ['VERB|Subcat=Intr'],
    'm  ON': ['NOUN|Gender=Masc'],
    'm  PN': ['PROPN|Gender=Masc'],
    'm u. adv': ['ADV', 'NOUN|Gender=Masc'],
    'm u. f': ['NOUN|Gender=Fem', 'NOUN|Gender=Masc'],
    'm': ['NOUN|Gender=Masc'],
    'm/coll': ['NOUN|Coll=Yes|Gender=Masc'],
    'm/f': ['NOUN|Gender=Fem', 'NOUN|Gender=Masc'],
    'm/pl': ['NOUN|Gender=Masc|Number=Plur'],
    'num': ['NUM'],
    'num.card': ['NUM|NumType=Card'],
    'num.ord': ['ADJ|NumType=Ord'],
    'onomat': ['INTJ'],
    'onomat.': ['INTJ'],
    'pl': ['NOUN|Number=Plur'],
    'pp': ['VERB|VerbForm=Part'],
    'prep': ['ADP'],
    'pron': ['PRON'],
    'pron. dem': ['PRON|PronType=Dem'],
    'pron. indef': ['DET|PronType=Ind'],
    'pron.dem': ['PRON|PronType=Dem'],
    'pron.indef': ['DET|PronType=Ind'],
    'pron.interrog': ['PRON|PronType=Int'],
    'pron.pers': ['PRON|PronType=Prs'],
    'pron.pers.': ['PRON|PronType=Prs'],
    'pron.pers.obj': ['PRON|PronType=Prs'],
    'pron.pers.pl': ['PRON|Number=Plur|PronType=Prs'],
    'pron.poss': ['DET|Poss=Yes|PronType=Prs'],
    'refl': ['VERB|Subcat=Refl'],
    'tr (bzw. intr.)': ['VERB|Subcat=Intr', 'VERB|Subcat=Tran'],
    'tr . 1. registrieren': ['VERB|Subcat=Tran'],
    'tr u. intr': ['VERB|Subcat=Tran', 'VERB|Subcat=Tran'],
    'tr u. refl sedistrigar': ['VERB|Subcat=Refl', 'VERB|Subcat=Tran'],
    'tr u. refl': ['VERB|Subcat=Refl', 'VERB|Subcat=Tran'],
    'tr': ['VERB|Subcat=Tran'],
    'tr. u. intr': ['VERB|Subcat=Intr', 'VERB|Subcat=Tran'],
    'tr.': ['VERB|Subcat=Tran'],
    'v': ['VERB'],
}


def cleanup_word(word):
    word = word.split(',')[0].strip()
    for suffix in SUFFIXES:
        if word.endswith(suffix):
            word = word[:-len(suffix)]
            break
    if word[-1] == '*':
        word = word[:-1]
    return word


def cleanup_pron(pron):
    pron = PRON_OVERRIDES.get(pron, pron)
    pron = pron.split(',')[0].split('/')[0].strip()
    if len(pron) > 0 and pron[-1] == '.':
        pron = pron[:-1]
    return pron


IPA_MAPPING = {
    ' ': ' ',
    '$': 'aː',   # asch
    '&': 'ŋ',    # adenliung
    '-': '.',    # consutsignar
    '3': 'ˈa',   # abandunau
    '6': 'ˈaː',  # abandunar
    '?': 'ˈeː',  # cateder
    'B': 'ɛ',    # accentuadamein
    'C': 'ɔː',   # chor
    'D': 'ˈɛ',   # abonnament, abscess
    'E': 'ˈɔː',  # anoda
    'F': 'ɛ',    # nuen (singleton word)
    'G': 'ɛː',   # bet
    'H': 'ˈɛː',  # acceder, affera
    'K': 'e',    # agregar, amfiteater
    'L': 'ˈe',   # adanfetg, alpetga
    'N': 'eː',   # crer, ler
    'O': 'ˈo',   # corresponder, schnoller
    'P': 'ˈeː',  # adulteri, atelier, attasche
    '\\': 'ˌo',  # navontanavos
    '_': 'ɔ',    # ambo, blanco
    'a': 'a',    # abrogaziun, abundonza
    'b': 'b',    # aba, abandun
    'c': 'k',    # cantadur, crappamorta, farmaceutica
    'd': 'd',    # abandun
    'e': 'e',    # abreviaziun, absentist
    'f': 'f',    # adanfetg, affatschar
    'g': 'g',    # agher, abrogar
    'h': 'h',    # alcohol, abstrahond
    'i': 'i',    # abdicar
    'j': 'j',    # abreviaziun
    'k': 'k',    # abdicar, acazia
    'l': 'l',    # labil
    'm': 'm',    # mader
    'n': 'n',    # naiv, nanna
    'o': 'o',    # obelisc, olimpic
    'p': 'p',    # palestra, perfetg
    'r': 'r',    # rapsodia, reavertura
    's': 's',    # sabotader, semantica
    't': 't',    # tabla, timid
    'u': 'u',    # udibel
    'v': 'v',    # vababund, vital
    'z': 'z',    # saletta, simar, suppa
    '~': 'ˈɔ',   # aberront
    '§': 'u',    # club, drun
    '©': 'ˈu',   # ucas, ultim
    '°': 'ˈʊ',   # uder, unda, pruir
    'º': 'uː',   # cusch, dur, ur
    'Ã': 'ʒ',    # aschadat, aschunscher, plascher
    'Æ': 'u̯',    # accentuar, zuav
    'Ï': 'ɛ̃',    # absint, bassin, gratin, satin, train
    'Õ': 'ə',    # absolutissem
    'Ø': 'ˈø',   # dumping, frondeur, snöber
    'ß': 'ˈʊː',  # buzra, dieschdubel, schuber
    'à': 'ˈi',   # miezmiur (singleton word)
    'á': 'ˈi',   # ablativ, adenliung
    'ã': 'ˈe',   # agrotecnicher
    'è': 'ˈiː',  # abbazia, adia
    'é': 'ˈe',   # eco, fonetic
    'ì': 'ˈo',   # bacteriologic
    'í': 'ɪ̯',    # uiest (singleton word)
    'ñ': 'ɲ',    # amogna, assignat
    'ò': 'ˈu',   # adut, bunamein, buob
    'ö': 'ø',    # flirt, pneu, puc, surf
    'ù': 'ˈuː',  # deluder, muzel
    'ú': 'ˈuː',  # actur, agressur
    'û': 'ʊ',    # brutg, cugn
    'ü': 'y',    # budgetar, jus
    'ÿ': 'd͡ʒ',   # jaz, jet, joint, schlampergiar
    '√': 't͡ʃ',   # tschacca, tschontschalom
    'ı': 'c',    # tgamin, tgil, tgutgaria
    'Œ': 'ˈøː',  # coiffeusa (singleton word)
    'ˆ': 'ɟ',    # gelatina, gelgia
    '›': 'ʎ',    # glienadi, glisch
    '≈': 'ʃ',    # scharfadad, schraffura
    '≠': 'iː',   # misch, pir, schi
    '≤': 'uː',   # sul (singleton word)
    '': 'a',    # abdicar, absurd, activ
    '‹': 'ˈøː',  # interpreneur, marodeur
    '‘': 'yː',   # ü!
}


RE_STRESS = re.compile(r'([^aeɛəioɔøuʊyUː]+)@')

# These were used to identify onsets and codas; not used anymore.
RE_ONSET = re.compile(r'^([^aeɛəioɔøuʊyˈ]+)')
RE_CODA = re.compile(r'[aeɛəioɔøuʊyU]ː?([^aeɛəioɔøuʊyUː]+)$')

ONSETS = set(
    "b bj bl br c d dj dl dr dz d͡ʒ f fj fl fr g gl gr h hj hr j k kl klj kn kr ks l lj "
    "m mj n nj p pj pl pn pr ps r rj s sb sf sfr sj sk sl sm sn sp st st͡s st͡sj "
    "t tj tr trj t͡s t͡sj t͡ʃ v vj vr "
    "z zj zv ɟ ɲ ʃ ʃc ʃf ʃfl ʃfr ʃk ʃkj ʃkl ʃkr ʃl ʃlj ʃm ʃn ʃp ʃpj ʃpl ʃpr ʃr ʃt ʃtj ʃtr ʃtrj ʃɲ ʃʎ "
    "ʎ ʒ ʒb ʒbl ʒbr ʒd ʒdr ʒg ʒgl ʒgr ʒl ʒv ʒvj ʒɟ".split())


CODAS = set(
    "b c cs d f fs ft ft͡s g k ks kst kt l lf lk lm lp lps ls lt lt͡s lt͡ʃ lʃ  "
    "m mb mf mn mp mps ms mt n nf nk nkt ns nt nt͡s nt͡ʃ nʃt p ps pt pʃt "
    "r rb rc rf rk rkt rl rls rm rn rns rp rps rpt rpʃ rs rt rt͡s rɲ rʃ rʃs rʃt s sk st t t͡s t͡sc t͡ʃ v "
    "z ŋ ŋk ŋks ŋkt ɲ ɲc ɲs ʃ ʃc ʃk ʃks ʃp ʃs ʃt ʃt͡s ʎ ʎs ʒd".split())


def move_stress(s):
    cluster = s.group(1)
    max_onset = ''
    for onset in ONSETS:
        if cluster.endswith(onset) and len(onset) > len(max_onset):
            candidate_coda = cluster[:-len(onset)]
            if candidate_coda == '' or candidate_coda in CODAS:
                max_onset = onset
    coda = cluster[:-len(max_onset)]
    if coda and coda not in CODAS:
        return '_[' + coda + '].' + max_onset + '_'
    return coda + 'ˈ' + max_onset

def make_ipa(pron):
    ipa = ''.join([IPA_MAPPING[k] for k in pron])
    ipa = ipa.replace('ts', 't͡s')
    ipa = IPA_OVERRIDES.get(ipa, ipa)
    if ipa.endswith('h'):  # systematic error in dictionary
        assert ipa[-2] in 'aɛeioɔuʊ'
        ipa = ipa[:-1] + 'ː'
    if 'ˈ' in ipa:
        acc = RE_STRESS.sub(move_stress, ipa.replace('ˈ', '@'))
        if acc[0] == '@':
            acc = 'ˈ' + acc[1:]
        ipa = acc.replace('@', 'ˈ')
    return ipa


RE_SPLIT_LEXEMES = re.compile(r'- (II|III|IV|V|VI|VII|VII|IX|X|XI|XII|XII)')

MISSING_GRAMMAR={}
def make_grammar(s):
    result = set()
    for lex in RE_SPLIT_LEXEMES.split(s):
        if lex.startswith('I '):
            lex = lex[2:]
        tag = lex.split(',')[0].split(' ->')[0].split(' ; ')[0]
        for gram in TAGS.get(tag, ['X']):
            if gram == 'X':
                MISSING_GRAMMAR[tag] = MISSING_GRAMMAR.get(tag, 0) + 1
            result.add(gram)
    return sorted(list(result))


def make_hunspell_dictionary_entry(word, grammar, ends_in_escha):
    if grammar.startswith('VERB'):  # TODO: Distinguish Subcat=Tran|Intr|Refl
        if word.endswith('tgar'):  # spetgar
            return '%s/9' % word
        if word.endswith('ignar'):  # cumpignar
            return '%s/10' % word
        if word.endswith('gar'):  # pagar
            return '%s/11' % word
        if word.endswith('ar'):
            if ends_in_escha:
                return '%s/8' % word  # skizzar
            else:
                return '%s/5' % word  # admirar
        if word.endswith('er'):  # vender
            return '%s/14' % word
        if word.endswith('ir'):
            if ends_in_escha:
                return '%s/16' % word  # capir
            else:
                return '%s/15' % word  # partir
    if grammar == 'NOUN|Gender=Fem':  # staila
        return '%s/1' % word
    if grammar == 'NOUN|Gender=Masc':  # caschiel
        return '%s/2' % word
    if grammar == 'ADJ':
        return '%s/3' % word
    if grammar == 'ADV':  # biaronz
        return '%s/4' % word
    if grammar == 'INTJ':  # assa
        return '%s/6' % word
    if grammar == 'NOUN|Coll=Yes|Gender=Fem':  # feglia
        return '%s/7' % word
    if grammar == 'NOUN|Coll=Yes' and word.endswith('a'):  # piaza
        return '%s/7' % word
    if grammar == 'NOUN|Gender=Fem|Number=Plur':  # capuns
        return '%s/17' % word
    if grammar == 'NOUN|Gender=Masc|Number=Plur':  # repressalias
        return '%s/18' % word
    if grammar == 'PROPN|Gender=Fem':  # Catrina
        return '%s/19' % word
    if grammar == 'PROPN|Gender=Masc':  # Carli
        return '%s/20' % word
    if grammar == 'PROPN':  # Habacuc, Gagl (all instances are masculine)
        return '%s/20' % word
    if grammar == 'ADP':  # sin
        return '%s/21' % word
    if grammar == 'CONJ':  # u
        return '%s/22' % word
    if grammar == 'NOUN|Coll=Yes|Gender=Masc':  # biestgam
        return '%s/23' % word
    if grammar == 'NUM|NumType=Card':  # otg
        return '%s/24' % word
    if grammar == 'NUM':  # treitschien
        return '%s/24' % word
    if grammar == 'ADJ|NumType=Ord':  # tschienavel
        return '%s/25' % word
    if grammar == 'PRON|PronType=Dem':  # quest
        return '%s/26' % word
    if grammar == 'PRON|PronType=Int':  # tgi
        return '%s/27' % word
    if grammar == 'ADJ|AdjType=Invar':  # extra
        return '%s/28' % word
    if grammar == 'DET|PronType=Ind':  # enqualche
        return '%s/29' % word
    if grammar == 'PRON|PronType=Prs':  # ti
        return '%s po:PRON uf:PronType=Prs'  % word
    if grammar == 'DET|Poss=Yes|PronType=Prs': # tes
        return '%s po:DET uf:Poss=Yes|PronType=Prs' % word
    if grammar == 'X':
        return word
    return word

RE_THIRD = re.compile(r'geschr. 3.: ([^\s,\)]+)')

def read_sql(path):
    for line in codecs.open(path, 'r', 'utf-8'):
        if line[0] != '(':
            continue
        id, ety, corp, pron, pron2, phras, word, word_de = eval(line.strip()[:-1])
        word = cleanup_word(word)
        if ' ' in word:
            continue  # almost all entries with spaces are conversion errors

        third = RE_THIRD.search(pron2)
        ends_in_escha = third and third.group(1).endswith('escha')
        if '<f>-D≈</f>' in pron2:
            ends_in_escha = True

        ipa = make_ipa(cleanup_pron(pron))
        grammar = make_grammar(corp)
        if False and word and ipa:
            for g in grammar:
                print ' '.join([word, g, ipa]).encode('utf-8')
        if True:
            for g in grammar:
                print(make_hunspell_dictionary_entry(word, g, ends_in_escha)).encode('utf-8')

    #print(sorted((n,t) for (t,n) in MISSING_GRAMMAR.items()))


if __name__ == '__main__':
    read_sql(sys.argv[1])
