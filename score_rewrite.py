
stopwords = set([w.strip() for w in open('stopwords.txt', 'r').readlines()])

def isStopWord(w): return w in stopwords

class AlignedSentence:
    def __init__(self, words, alignments, alignedTo, flipAlignmentDirection=False):
        if isinstance(words, str): words = words.split()
        if isinstance(alignments, str): alignments = alignments.split()
        if isinstance(alignedTo, str): alignedTo = alignedTo.split()
        if isinstance(alignedTo, AlignedSentence): alignedTo = alignedTo.w
        self.w = words
        self.src = alignedTo
        self.a = { n: set() for n in xrange(len(self.w)) }
        for a in alignments:
            if isinstance(a, str):
                [src,tgt] = map(int, a.split('-'))
                src -= 1
                tgt -= 1
            else:
                [src,tgt] = a
            if flipAlignmentDirection: src,tgt = tgt,src
            if src < 0 or src >= len(words):
                raise Exception('got alignment for source word ' + str(src) + ' but |words| = ' + str(len(words)))
            if tgt < 0 or tgt >= len(alignedTo):
                raise Exception('got alignment for target word ' + str(tgt) + ' but |alignedTo| = ' + str(len(alignedTo)))
            self.a[src].add(tgt)

    def __str__(self):
        out = ''
        for n,w in enumerate(self.w):
            if n > 0: out += ' '
            out += w + '_' + ('{}' if len(self.a[n]) == 0 else ','.join(map(str,self.a[n])))
        return out
    
    def __repr__(self): return str(self)

def composeAlignment(a0, a1): # returns a3 such that a3[i] = a0[a1[i]], plus the set of indices j such that a0[j] != {} but a1 doesn't "use" j -- i.e., there is no i such that a1[i] == j
    a3words = a1.w
    a3src   = a0.src
    a3aln   = [ (n,j) for n,a in a1.a.iteritems() for i in a for j in a0.a[i] ]
    allA0   = set([i for i,a in a0.a.iteritems() if len(a) > 0])
    usedA0  = set([i for n,a in a1.a.iteritems() for i in a])
    droppedA0 = allA0 - usedA0
    return AlignedSentence(a3words, a3aln, a3src), droppedA0

#      1   2    3   4      5      6       7
ja  = 'i tasty big messy purple sandwich ate .'.split()
#                      1  2  3   4    5    6     7       8
en0 = AlignedSentence('i ate a tasty big messy purple sandwich', '1-1 2-7 4-2 5-3 6-4 7-5 8-6', ja)
#                      1   2    3    4     5       6      7    8   9  10
en1 = AlignedSentence('a tasty big messy purple sandwich was eaten by me', '1-3 2-4 3-5 4-6 5-7 6-8 8-2 10-1', en0)
#                      1  2  3    4      5    6    7    8    9    10   11
en2 = AlignedSentence('i ate a sandwich that was tasty big messy and purple', '1-1 2-2 3-3 4-8 7-4 8-5 9-6 11-7', en0)
#                      1   2      3      4    5   6  7
en3 = AlignedSentence('a tasty sandwich was eaten by me', '1-3 2-4 3-8 5-2 7-1', en0)

def pseudoDecalage(alnList):  # aln list should be sorted like: [(0, set([])), (1, set([1])), (2, set([5])), (3, set([])), (4, set([6])), ...]
    curPosInSrc = 1
    decalage = 0
    for tgtPos, alignment in alnList:
        # in order to produce tgtPos, we have to wait until the _last_ aligned word
        if len(alignment) == 0: continue
        srcPos = max(alignment)
        decalage += max(0, srcPos - curPosInSrc)
        curPosInSrc = max(curPosInSrc, srcPos)
        curPosInSrc += 1   # we've spoken a word so we get another word "for free"
    return decalage
        

def score(a0, a1):
    comp,drop    = composeAlignment(a0, a1)
    droppedWords = [a0.w[i] for i in drop]
    numDropped   = len(droppedWords)
    numDroppedContent = len([w for w in droppedWords if not isStopWord(w)])
    alnList = comp.a.items()
    alnList.sort()
    decalage = pseudoDecalage(alnList)
    
    return numDropped, numDroppedContent, decalage

#composed1,dropped1 = composeAlignment(en0, en1)
#composed2,dropped2 = composeAlignment(en0, en2)
#composed3,dropped3 = composeAlignment(en0, en3)

print score(en0, en1), en1
print score(en0, en2), en2
print score(en0, en3), en3
