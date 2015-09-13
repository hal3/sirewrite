import sys

try:
    from sayit import sayit
except ImportError:
    print >>sys.stderr, 'warning: sayit unavailable, defaulting to 500ms words'
    def sayit(lang,words): return max(0., 0.4454785 * len(words) - 0.116751)

#def sayit(lang,words): return float(len(words))
        
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
ja  = 'i tasty big messy purple sandwich ate'.split()
#                      1  2  3   4    5    6     7       8
en0 = AlignedSentence('i ate a tasty big messy purple sandwich', '1-1 2-7 4-2 5-3 6-4 7-5 8-6', ja)
#                      1   2    3    4     5       6      7    8   9  10
en1 = AlignedSentence('a tasty big messy purple sandwich was eaten by me', '1-3 2-4 3-5 4-6 5-7 6-8 8-2 10-1', en0)
#                      1  2  3    4      5    6    7    8    9    10   11
en2 = AlignedSentence('i ate a sandwich that was tasty big messy and purple', '1-1 2-2 3-3 4-8 7-4 8-5 9-6 11-7', en0)
#                      1   2      3      4    5   6  7
en3 = AlignedSentence('a tasty sandwich was eaten by me', '1-3 2-4 3-8 5-2 7-1', en0)



def pseudoDecalage(aln): # returns both total decalage and total speaking time for E
    #
    # the decalage (ear-voice span) for some english word e is the
    # difference in time between the START time of that english word
    # and the END time of the last japanese word it's aligned to
    #
    # for instance, given:
    #    WATASHI-WA    HARU    DESU
    #  0            t1      t2      t3
    #   <====>
    #       I       AM      HAL
    #  T0      T1       T2       T3
    #
    # with the obvious alignment, the decalage for each English word is:
    #
    #   I    : T0 - t1
    #   AM   : T1 - t3
    #   HAL  : T2 - t2
    #
    # assuming speaking happens as soon as the aligned word is done,
    # and any previously spoken english word is done:
    #
    #   T0 = t1
    #   T1 = max( t3, T0+len("I") )
    #   T2 = max( t2, T1+len("AM") )
    #
    # so, generalizing, we have:
    #
    #    t[i]   = time point BEFORE J[i] is spoken; ergo t[i+1] = time point AFTER J[i] is spoken
    #    T[j]   = time point BEFORE E[j] is spoken
    #    T[-1] + sayit(e[-1]) == total time to say E
    #
    #    t[i]   = sayit(j[:i])
    #    T[0]   = max(t[A[0]+1])            | +1 is because it's END of this word, (*)
    #    T[j+1] = max(T[j] + sayit(E[j]),   | can say it right after E[j] is done being spoken
    #                 t[A[j+1]+1] )         | or have to wait for the corresponding J to finish
    #
    # (*) in the case of null alignments (ie A[j] == {}), we pretend
    #     the null-aligned word has the same maximum alignment as the
    #     previous word (equivalent to aligning to J[0])
    ja = aln.src
    en = aln.w
    t  = [sayit('ja', ja[:i]) for i in range(len(ja)+1)]
    A  = [ 0 if len(aset)==0 else max(aset) for j,aset in aln.a.iteritems() ]
    T  = [ t[A[0]+1] ]
    for j in range(len(en)-1):
        T.append( max( T[j] + sayit('en-US',[en[j]]), t[A[j+1]+1] ) )
    T.append( T[-1] + sayit('en-US', en[-1]) )
    return sum(T) - sum(t), T[-1]

def score(a0, a1=None):
    comp,drop = (a0,[]) if a1 is None else composeAlignment(a0, a1)
    droppedWords = [a0.w[i] for i in drop]
    numDropped   = len(droppedWords)
    numDroppedContent = len([w for w in droppedWords if not isStopWord(w)])
    decalage,totalTime = pseudoDecalage(comp)
    
    return numDropped, numDroppedContent, decalage, totalTime

#composed1,dropped1 = composeAlignment(en0, en1)
#composed2,dropped2 = composeAlignment(en0, en2)
#composed3,dropped3 = composeAlignment(en0, en3)

print score(en0), en0
print score(en0, en1), en1
print score(en0, en2), en2
print score(en0, en3), en3
