#Author: Cason White
#File: Preprocessor.py
#Description: A class that tokenizes text documents and optionally removes stopwords, as well as stems words.


import time
import os
import string
import math
import nltk
import json
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from operator import itemgetter
import xml.etree.ElementTree as ET


class Preprocessor:

	#init requires the working directory for either where the requisite JSON file is stored or where the folder of documents is stored
	def __init__(self, p):
		self.folderPath = p
		self.fileText = ""
		self.textDict = {}
		self.docDict = {}
		self.idfDict = {}
		#self.isCollectionFromJson = False

	#tokenizes all the files in the given directory. set stemming to 1 if you want stopwords removed and the stemmer implemented.
	def tokenizeFiles(self, stemming=1, isXml=0):
		print("Tokenizing collection...")
		os.chdir(self.folderPath)
		for filename in os.listdir(self.folderPath):
			self.docDict[filename] = {}
			self.readFile(filename)
			self.processFile(filename, stemming, isXml)
		
		if ' ' in self.textDict:
			del self.textDict[' ']

		if '' in self.textDict:
			del self.textDict['']
		print("\tTokenizing Completed")

	#tokenizes a given JSON file with the format
	#[{"title": "x1", "url": "x2", "summary": "x3"}, {"title": "y1", "url": "y2", "summary": "y3"}, ...]
	def tokenizeJson(self, filename, stemming=1,isXml=0):
		self.isCollectionFromJson = True
		print("Loading JSON collection...")
		os.chdir(self.folderPath)
		with open(filename, encoding='utf-8') as f:
			collection = json.load(f)
		print("\tDone")

		print("Tokenizing Collection...")
		for entry in collection:
			self.docDict[entry["url"]] = {"TITLE_NAME" : entry["title"]}
			self.fileText = entry["summary"]
			self.processFile(entry["url"], stemming, isXml)


		if ' ' in self.textDict:
			del self.textDict[' ']

		if '' in self.textDict:
			del self.textDict['']
		print("\tTokenization Completed")

	#takes a file and copies it's contents to the fileText variable for later processing
	def readFile(self, file):
		with open(file) as f:
			self.fileText = f.read();


	#tokenizes a file and adds it to the collection, set stemming to 1 if you want stopwords removed and the stemmer implemented.
	def processFile(self, filename, stemming, isXml):
		#print("\tProcessing " + filename + "...", end="")

		if isXml == 1:
			tree = ET.fromstring(self.fileText)
			fileText = ET.tostring(tree, encoding='utf-8', method='text')

		text = self.fileText.lower().translate(self.fileText.maketrans('', '', "-\'\t\n")).translate(self.fileText.maketrans(string.punctuation, ' '*len(string.punctuation))).split(" ")
		if stemming == 1:
			ps = PorterStemmer()
		for i in text:
			if stemming == 1:
				if i in stopwords.words("english"):
					continue
				else:
					i = ps.stem(i)
			if i not in self.textDict:
				self.textDict[i] = 1
			else:
				self.textDict[i] += 1

			if i not in self.docDict[filename]:
				self.docDict[filename][i] = 1
			else:
				self.docDict[filename][i] += 1
		#print("\t\tDone")


	#creates a tfidf matrix using the collected documents
	def makeTfidfMatrix(self):
		print("Making tfidf matrix...")
		for word in self.textDict:

			self.idfDict[word] = math.log(len(self.docDict) / self.textDict[word], 2)

			for doc in self.docDict:
				if word in self.docDict[doc]:
					self.docDict[doc][word] = self.docDict[doc][word] * self.idfDict[word]


		print("\tDone")

	#cleans and tokenizes a query, then transforms it into a tfidf vector for processing
	def tfidfQuery(self, query):
		ps = PorterStemmer()
		queryDict = {}
		queryArray = query.lower().translate(self.fileText.maketrans('', '', "-\'\t\n")).translate(self.fileText.maketrans(string.punctuation, ' '*len(string.punctuation))).split(" ")


		for unstemWord in queryArray:
			word = ps.stem(unstemWord)
			if word in self.textDict:
				if word in queryDict:
					queryDict[word] += 1
				else:
					queryDict[word] = 1

		for word in queryDict:
			queryDict[word] = (queryDict[word] / self.textDict[word]) * self.idfDict[word]
		return queryDict

	#gets the length for the cosign similarity formula given a vector(dictionary)
	def length(self, dic):
		dicsquared = 0
		for word in dic:
			if word == "TITLE_NAME":
				continue

			dicsquared += (dic[word] ** 2)

		return math.sqrt(dicsquared)


	#calculates the cosign similarity between a query vector and a given document
	def cosSim(self, queryDict, doc):
		queryLength = self.length(queryDict)
		docLength = self.length(self.docDict[doc])
		top = 0
		for word in queryDict:
			if word in self.docDict[doc]:
				top += (queryDict[word] * self.docDict[doc][word])

		#print(top)
		#print(queryLength)
		#print(docLength)
		try:
			return top / (queryLength * docLength)
		except ZeroDivisionError:
			#print("division by zero")
			return 0

	#calculates the cosign similarity for all documents in the collection given a query, then puts the results in an ordered dictionary and returns it
	def processQuery(self, query):
		print("\tProcessing Query " + query + "...")
		# start = time.time()
		resultDict = {}
		titleDict = {}
		queryDict = self.tfidfQuery(query)

		if self.isCollectionFromJson == True:
			for doc in self.docDict:
				if doc == "TITLE_NAME":
					continue
				#resultDict[doc] = {"cossim": self.cosSim(queryDict, doc), "title": self.docDict[doc]["TITLE_NAME"]}
				resultDict[doc] = self.cosSim(queryDict, doc)
				titleDict[doc] = self.docDict[doc]["TITLE_NAME"]

		for doc in self.docDict:

			resultDict[doc] = self.cosSim(queryDict, doc)

		# resultDict["time"] = time.time() - start

		return (titleDict, dict(sorted(resultDict.items(), key = itemgetter(1), reverse = True)[:10]))


		print("\t\tDone")

	#uses processQuery on a given list of queries to calculate
	def processQueries(self, queryList):
		print("Processing list of queries...")
		resultsDict = {}
		if self.isCollectionFromJson == True:
			for query in queryList:

				resultsDict[query] = self.processQuery(query)

		else:

			for query in queryList:
				resultsDict[query] = self.processQuery(query)

		print("\tDone")
		return resultsDict
		

	#gets the top n words in the collection sorted in reverse order by their number of occurences
	def getTopN(self, n):
		return dict(sorted(self.textDict.items(), key = itemgetter(1), reverse = True)[:n])

	#gets the total word count of the dictionary
	def getWordCount(self):
		count = 0
		for key, value in self.textDict.items():
			count += value
		return count 

	#counts the amount of keys in the textDict dictionary
	def getKeyCount(self):
		return len(self.textDict)

	#gets the minimum number of unique words accounting for 15% of the total number of words in the collection.
	#returns a tuple in the form of (# of unique words, their count, 15% of the total # of words in the collection)
	def get15WordCount(self):
		Total15WordCount = self.getWordCount() * .15
		wordCount = 0
		count = 0
		sortedDict = dict(sorted(self.textDict.items(), key = itemgetter(1), reverse = True))
		for key in sortedDict:
			if wordCount >= Total15WordCount:
				break
			else:
				count += 1
				wordCount += sortedDict[key]

		return (count, wordCount, Total15WordCount)


	#export all class dictionaries to a file as JSON for later loading
	def exportDicts(self, filename):
		print("Exporting Dictionaries to " + filename + "...")
		exportDict = {}
		exportDict["textDict"] = self.textDict
		exportDict["docDict"] = self.docDict
		exportDict["idfDict"] = self.idfDict
		exportDict["isCollectionFromJson"] = self.isCollectionFromJson
		with open(filename, 'w', encoding="utf-8" ) as f:
			json.dump(exportDict, f)

		print("\tDone")

	#import all dictionaries from JSON file
	def importDicts(self, filename):
		print("Importing Dictionaries from " + filename + "...")
		with open(filename, encoding="utf-8",) as f:
			importDict = json.load(f)

		self.textDict = importDict["textDict"]
		self.docDict = importDict["docDict"]
		self.idfDict = importDict["idfDict"]
		self.isCollectionFromJson = importDict["isCollectionFromJson"]

		print("\tDone")

if __name__ == "__main__":
	#open the list of queries for reading
	#with open("queries.txt") as text:
	#	queries = text.read()

	#queries = queries.split(".")
	#removes the empty last option
	#queries.pop()

	#tokenize, create the tfidf matrix, and finally process all the queries and store the results in resultDict
	#stemdict = Preprocessor(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cranfieldDocs"))
	#stemdict.tokenizeFiles(1,1)

	stemdict = Preprocessor(os.path.dirname(os.path.abspath(__file__)))
	# stemdict.tokenizeJson("wiki.json", 1, 0)
	# stemdict.makeTfidfMatrix()
	# stemdict.exportDicts("bigBoi.json")

	#stemdict.importDicts("result.json")
	#titles, result = stemdict.processQuery("The Communist Party")

	#resultsDict = stemdict.processQueries(queries)


	#place the results in text files matching the name of each query
	#print("Creating output text files...")
	#for query in resultsDict:
	#	with open("../" + query[1:] + ".txt", 'w') as f:
	#		for doc in resultsDict[query]:
	#			f.write(query + " " + doc + " " + str(resultsDict[query][doc]) + "\n")

	file = input("Enter input JSON file (in current directory): ")
	stemdict.importDicts(file)
	while(True):
		query = input("Enter a query to test: ")
		titles, output = stemdict.processQuery(query)

		for url in output:
			print(titles[url] + " " + url)

		print("\n")
		cont = input("Do you wish to test another query? <y/n> ")

		if cont == 'n':
			break


	# print("Done.")
	# print("Finished!")
