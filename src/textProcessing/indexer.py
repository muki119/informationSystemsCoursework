import concurrent.futures
from collections import Counter

import bs4

from commonUtilities import commonUtilities
from textProcessing import invertedIndex


class Indexer:
    """
        This class Builds the inverted index and metadata dictionary for the collection of documents.
    """
    def __init__(self,path:str,stemmed:bool=False):
        self.index:invertedIndex.InvertedIndex = invertedIndex.InvertedIndex(path)
        self.stemmed:bool = stemmed
        
    def getIndex(self)->invertedIndex.InvertedIndex:
        return self.index
    
    def getMetadata(self)->invertedIndex.InvertedIndex:
        return self.index.getMetadata()
    
    def buildIndex(self,forceRebuild:bool = False):
        try:
            if not self.index.isEmpty() and not forceRebuild:
                print("Index Ready")
                return
            with open('src/videogame-labels.csv') as videogameLabels :
                videogamesLine = videogameLabels.readlines()[1:]#ignore first line which is just formatting  
            
            print("Reading and Processing files...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor: #multithreading to speed up the process  
                executor.map(self.__processPage,videogamesLine) # tells threads to process the pages in the list
                
            print("Building Index")
            self.index.displayDictionary() #create a output file of the index
            self.index.dumpDictionary() #save the index to a file
            print("Done")
        except Exception as e:
            print("Error While Building Index")
            print(e)
    
    def __processPage(self,pageLineInfo):
        """Processes a page and adds the data to the index"""
        try:
            pageData = pageLineInfo.rstrip().split(",") #split the page metadata
            pageText:str = self.__openPage(pageData) #open the page , clean it and get the text within it 
            tokenFreqdist:dict = self.__createTokens(pageText,self.stemmed) # create tokens ftom the text and get the frequency of each token ,store in a dictionary.
            metadataTuple=[]
            for val in pageData[1:]: # tokenise metadata and put it into a tuple
                metadataTuple+=commonUtilities.CommonUtilities.tokenizeString(val)
            for token , freq in tokenFreqdist.items():
                self.index.addWord(token,pageData[0],freq,[1,2,4,5,6],tuple(metadataTuple)) #add the token data to the index.
        except Exception as e:
            print("Error While Processing Page",e)
            print(f'error data {pageLineInfo}')

    def __openPage(self,pageLineInfo:list[str])->str:
        try:
            # url,STRING : esrb,STRING : publisher,STRING : genre,STRING : developer
            var1  = pageLineInfo[0].split("/")
            pageurl = "src/videogames"+"/"+var1[-1]
            with open(pageurl) as videogamePage: #open the html file
                return self.__cleanPage(videogamePage) #clean the page and return the text within it
        except Exception as e:
            print("Error While Opening Page")
            print(f'error data {pageLineInfo}')

    def __cleanPage(self,page)->str:
        try:
            bs4page= bs4.BeautifulSoup(page,"html5lib")
            for scriptsAndStyles in bs4page(["script","style","noembed",'noscript']): #remove scripts and styles and other non text elements
                scriptsAndStyles.decompose()
            for menuLeft in bs4page.find_all("div", {"id": "menuLeft"}): # remove divs with class 'menuLeft'
                menuLeft.decompose()
            for requirements in bs4page.find_all("div", {"class": "gameBioSysReq"}): # remove divs with class 'menuLeft'
                requirements.decompose()
            pageText:str= bs4page.get_text(separator="\n",strip=True) #get the text from the page
            return pageText
        except Exception as e:
            print("Error While Cleaning Page",e)

    def __createTokens(self,pageText:str ,stemmed = False)-> dict:
        try:
            tokenizedLemmatizedText = commonUtilities.CommonUtilities.tokenizeString(pageText)# tokenizes and lemmatized the Incomming text -filtered to remove stopwords and insignificant charachters removes any annoying charachters too.
            tokenizedStemmedText = commonUtilities.CommonUtilities.stemmedTokenizeString(pageText)
            wordTokenFrequencyDictionary = Counter(tokenizedLemmatizedText if not stemmed else tokenizedStemmedText) #store frequency of those lemmitized words
            return wordTokenFrequencyDictionary
        except Exception as e:
            print("Error While Creating Tokens")

# test = Indexer('src/wordIndex.pk1')
# ttext = test.openPage(["videogame/ps2.gamespy.com/zatch-bell.html","Teen","Bandai","Fighting","Eighting"])
# test.createTokens(ttext)
# tokenDictionary{
#     word:{
#         totalDocumentFrequency:int,
#         postings:{
#             documentName:{
#                 occurances:int,
#                 positions:[]
#                             }
#         }
#     }
# }

