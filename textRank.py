import nltk
import re
import networkx as nx
import signal
import math
import io
import os
import sys

# split text into sentences
def splitSentence(text):
    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    text = ' '.join(text.split())

    sentences = re.split(r' *[\.\?!][\'\"\)\]]* +', text)

    for sentence in sentences:
        if sentence.strip() == '':
            sentences.remove(sentence)

    sentences = ['{0}.'.format(sentence) for sentence in sentences]
    return sentences

# read file
def readFile(path):
    text = ''.join(open(path).readlines())
    return text

# get all words in text
def words(text):
    tokens = nltk.word_tokenize(text)
    punctuation = ['!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';',
                   '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~', '\n', '”']

    for token in tokens:
        if token in punctuation:
            tokens.remove(token)
    return tokens

# filter sentence with stop words
def filterStopwords(sentences, stopWords):
    list = []
    for sentence in sentences:
        str = ""
        for wd in words(sentence):
            if wd not in stopWords:
                str = str + " "+ wd
        list.append(str)
    return list

# assign POS tags to the filtered words
def posTag(filtersentence):
    tagged = []
    for sentence in filtersentence:
        word = words(sentence.lower())
        tagged.append(nltk.pos_tag(word))
    return tagged

# filter nouns and adjectives
def filterTag(tagged):
    filtered = []
    for sentence in tagged:
        temp = []
        for word in sentence:
            if word[1] in ['NN', 'NNP','JJ']:
                temp.append(word[0])
        filtered.append(temp)
    return filtered

# get all different words, get vertices for keyword extraction
# input: filtered, list of list
def difWord(filtered):
    list = []
    for item in filtered:
        for word in item:
            if item is not '':
                list.append(word.lower())
    setOfWord = set(list)
    return setOfWord

# co-occurrence relation with a window of N words, set N as 2
def getEdge(filtered):
    list = []
    for item in filtered:
        lenOfItem = len(item)
        if item is not '' and lenOfItem > 1:
            for i in range(lenOfItem - 1):
                list.append((item[i].lower(), item[i+1].lower()))
    return list

# build graph
def buildGraph(vertices, edges):
    # undirected graph
    graph = nx.Graph()
    for vertice in vertices:
        graph.add_node(vertice)
    for edge in edges:
        # can change weight (Levenshtein distance)
        graph.add_edge(edge[0], edge[1], weight = 1)
    return graph

# get most important N words from dictionary
def getMost(sortedDic, n):
    nItems = sortedDic[:n]
    keyWords = []

    i = 0
    while i < n:
        keyWords.append(nItems[i][1])
        i = i + 1
    return keyWords

# change N as an input
def getTopWord(N, sortedKeyWords, filtered):

    # check if N is available
    if(N < len(sortedKeyWords)):
        topWords = getMost(sortedKeyWords, N)
        signal.alarm(5)

        try:
            modifiedKeyWords = joinWords(topWords, filtered)

            return [topWords, modifiedKeyWords]

        except TimeoutException:
            print("Can not get modified key words!")
            return [topWords, None]

    else:
        print("Please try smaller N value.")

# check if results are adjacent words in filtered sentences list
# every sentence : [w1, w2, w3, ...]
# topWords: [A, B, C, ...]
def joinWords(topWords, filterSentences):
    phrase = []
    for sentence in filterSentences:
        currentIndex = 0
        nextIndex = 1
        startIndex = []
        endIndex = []

        lengthOfSentence = len(sentence)

        if lengthOfSentence > 1:
            while nextIndex < (lengthOfSentence):
                currentWord = sentence[currentIndex].lower()
                nextWord = sentence[nextIndex].lower()

                if currentIndex == 0:
                    if currentWord in topWords and nextWord in topWords:
                        startIndex.append(0)
                elif currentIndex > 0 and lengthOfSentence > 2 and currentIndex < lengthOfSentence - 1:
                    if currentWord in topWords and nextWord in topWords and sentence[currentIndex-1].lower() not in topWords:
                        startIndex.append(currentIndex)

                if lengthOfSentence == 2:
                    if currentWord in topWords and nextWord in topWords:
                        endIndex.append(nextIndex)

                if len(sentence) > 2:
                    if (nextIndex == (lengthOfSentence - 1)):
                        if currentWord in topWords and nextWord in topWords:
                            endIndex.append(nextIndex)
                    elif (currentWord in topWords and nextWord in topWords and sentence[nextIndex+1].lower() not in topWords):
                        endIndex.append(nextIndex)

                currentIndex = currentIndex + 1
                nextIndex = nextIndex + 1

        # if there is phrase exists
        # extract phrases using index of starts and ends
        plist = []
        if(len(startIndex) > 0 and len(startIndex) == len(endIndex)):
            numOfPhrase = len(startIndex)
            for i in range(numOfPhrase):
                tempPhrase = ""
                s = startIndex[i]
                e = endIndex[i]

                for wd in range(s, e+1):
                    if sentence[wd].lower() not in plist:
                        tempPhrase = tempPhrase + sentence[wd]
                        plist.append(sentence[wd].lower())
                        tempPhrase = tempPhrase + ' '

                if(len(tempPhrase) > 0):
                   if(tempPhrase[len(tempPhrase)-1] == ' '):
                       tempPhrase = tempPhrase[:-1]

            if(' ' in tempPhrase):
                phrase.append(tempPhrase)

        # d is dictionary of phrases
        d = dict()
        for ph in phrase:
            if ph not in d:
                d[ph] = 1
            else:
                d[ph] += 1

    sortedPhrase = sorted([(value, key) for (key, value) in d.items()], reverse=True)
    sortedPhraseValue = []
    for i in range(len(sortedPhrase)):
        sortedPhraseValue.append(sortedPhrase[i][1])

#    print(sortedPhrase)

    modifyPs = []

    index = 0
    while(index < (len(topWords))):
        spv = 0
        while (spv < len(sortedPhraseValue)):
            if(topWords[index] in sortedPhraseValue[spv].lower()):
                modifyPs.append(sortedPhraseValue[spv])
                index = index + 1
                break
            else:
                spv = spv + 1

    modifyPs = set(modifyPs)
    finalPs = list(modifyPs)

    oneWord = []

    for wd in topWords:
        flag = 0
        for pr in range(len(finalPs)):
            if wd in finalPs[pr].lower():
                flag = 1
        if flag == 0:
            oneWord.append(wd)
#    print(oneWord)

    finalPs.extend(oneWord)

    return finalPs

###################################################
# functions for document summarization

# build dictionary of sentence
def buildDic(disSens):
    sizeOfSentence = len(disSens)
    data = dict()

    i = 0
    j = 1

    while j < sizeOfSentence:
        keyOfDic = (disSens[i], disSens[j])
        valueOfDic = similarity(disSens[i], disSens[j])

        data[keyOfDic] = valueOfDic

        i = i + 1
        j = j + 1

    return data

# get similarity of two sentences
def similarity(sentence1, sentence2):

    disWord1 = distinctWord(sentence1)
    disWord2 = distinctWord(sentence2)

    numOverlap = overlap(disWord1, disWord2)
    lenOf1 = len(disWord1)
    lenOf2 = len(disWord2)

    log1 = math.log2(lenOf1)
    log2 = math.log2(lenOf2)

    if (log1 + log2) == 0:
        numSimilarity = 0
    else:
        numSimilarity = float(numOverlap)/float(log1 + log2)

    return numSimilarity

# get all different words
# input: a sentence
def distinctWord(sentence):
    wordlist = words(sentence)
    list = []
    for word in wordlist:
        if word is not '':
            list.append(word.lower())
    setOfWord = set(list)
    return setOfWord

# get distinct sentence, vertices for document summarization
def distingSen(listOfSentences):
    list = []
    for sentece in listOfSentences:
        if sentece not in list:
            list.append(sentece)
    return list

# overlap number of two sentences sets
def overlap(wordlist1, wordlist2):

    numOfOverlap = 0

    for dif1 in wordlist1:
        if dif1 in wordlist2:
            numOfOverlap = numOfOverlap + 1

    return numOfOverlap

# build graph for document
# if similarity> 0.5, weight = similarity
def graphDoc(distictSentence, dicDoc):
    # undirected graph
    graph = nx.Graph()

    for s in distictSentence:
        graph.add_node(s)
    for key in dicDoc:
        if dicDoc[key] > 0.5:
            graph.add_edge(key[0], key[1], weight = dicDoc[key])

    return graph

def getTopSentence(M, sortedSentence):

    # check if M is available
    if(M < len(sortedSentence)):
        signal.alarm(10)
        try:
            topSentence = getMost(sortedSentence, M)
            return topSentence

        except TimeoutException:
            print("Sorry, run out of time! Can not get modified key words! Please try larger or smaller M value.")
            return None
    else:
        print("Please try small M value.")

# concatenate sentence in list
def getSummarization(topList):
    result = ""
    for sentence in topList:
        result = result + sentence + " "
    if (result[len(result) - 1] == ' '):
        result = result[:-1]
    return result

#################################
#  control run time

# Custom exception class
class TimeoutException(Exception):
    pass

# Custom signal handler
def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

###########################################

def writeFile(filename, topWord, modifiedKeyWords, summarization, N):
    print("Generating output to " + 'result/' + filename)
    if not os.path.exists("result/"):
        os.makedirs("result/")
    resultFile = io.open('result/' + filename, 'w')

    string1 = "These are top %s key words:" % N
    resultFile.write(string1)
    resultFile.write('\n')
    string2 = "" + ", ".join(str(e) for e in topWord[0])
    resultFile.write(string2)
    resultFile.write('\n\n')

    if modifiedKeyWords is not None:
        string3 = "These are modified key words:"
        resultFile.write(string3)
        resultFile.write('\n')
        string4 = "" + ", ".join(modifiedKeyWords)
        resultFile.write(string4)
        resultFile.write('\n\n')

    if summarization is not None:
        string5 = "These are document summary:"
        resultFile.write(string5)
        resultFile.write('\n')
        string6 = "".join(summarization)
        resultFile.write(string6)

    resultFile.close()

###########################################

def main(argv = sys.argv):
    if(len(argv) == 5):

        fileName = argv[1]
        text = readFile(fileName)
        stopPath = argv[2]
        stopWords = readFile(stopPath).split("\n")

        sentences = splitSentence(text)

        # keyphrase extraction
        # filter sentence with stop words
        filtersentence = filterStopwords(sentences, stopWords)

        # assign POS tags to sentence
        tagged = posTag(filtersentence)

        # filter nouns and adjectives
        filtered = filterTag(tagged)

        # get vertices for keyword
        vertices = difWord(filtered)

        # get edges for keyword
        edges = getEdge(filtered)

        # build graph for keyword
        graph = buildGraph(vertices, edges)

        # pageRank
        pageRanked = nx.pagerank(graph, alpha=0.85, tol=0.0001, weight='weight')

        # sort key words
        sortedKeyWords = sorted([(value, key) for (key, value) in pageRanked.items()], reverse=True)

        # get most important N words from dictionary, N = 5
        N = int(argv[3])

        topWord = getTopWord(N, sortedKeyWords, filtered)

        if (topWord is not None):
            modifiedKeyWords = topWord[1]

        # document summarizaion
        # filtered: use this to build graph ------> sentences: original sentences

        # vertices for documents
        distictSentence = distingSen(sentences)

        dicDoc = buildDic(distictSentence)

        graphForDoc = graphDoc(distictSentence, dicDoc)

        # pageRank for document summarization
        pageRankedDoc = nx.pagerank(graphForDoc, alpha=0.85, tol=0.0001, weight='weight')

        sortedSentence = sorted([(value, key) for (key, value) in pageRankedDoc.items()], reverse=True)

        # get most important M sentences
        M = int(argv[4])

        topList = getTopSentence(M, sortedSentence)
        if topList is not None:
            summarization = getSummarization(topList)

        path, filename = os.path.split(fileName)

        writeFile(filename, topWord, modifiedKeyWords, summarization, N)


    else:
        print("Wrong input!")

if __name__ == "__main__":
    main()