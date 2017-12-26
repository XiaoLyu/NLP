# NLP
This is a project for NLP course. It is a Automatic Text Summarization System based on TextRank algorithm.

Python version: Python 3.6.1

how to run:
python3 textRank.py <pathOfTestDocument> <stopWordsPath> N M

where N is the length of key words we want to get and M is the number of key sentence we want to extract.

for example:
python3 textRank.py "resource/Corpus.txt" "resource/stopWords.txt" 10 2
