
# coding: utf-8

'''
open results in praat

visualizes errors for different as graph. matplotlib
'''
import sys
import os
from Phonetizer import Phonetizer
parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0]) ), os.path.pardir)) 

#  evaluation  
pathEvaluation = os.path.join(parentDir, 'AlignmentEvaluation')
if not pathEvaluation in sys.path:
    sys.path.append(pathEvaluation)


from PraatVisualiser import addAlignmentResultToTextGrid, openTextGridInPraat, addAlignmentResultToTextGridFIle, \
  _alignmentResult2TextGrid

from tab2PraatAndOpenWithPRaat import tab2PraatAndOpenWithPRaat 

from TextGrid_Parsing import tier_names


# In[2]:

import matplotlib.pylab as plt
import numpy as np
ANNOTATION_EXT = '.TextGrid'  

def determineSuffix(withDuration, evalLevel):
    
    evalLevelToken = tier_names[evalLevel]
    if withDuration:
        if Phonetizer.withSynthesis:
            tokenAlignedSuffix =  '.' + evalLevelToken + 'DurationSynthAligned'
            phonemesAlignedSuffix = '.phonemesDurationSynthAligned'
        else:
            tokenAlignedSuffix = '.' + evalLevelToken + 'DurationAligned'
            phonemesAlignedSuffix = '.phonemesDurationAligned'
    else:
        tokenAlignedSuffix = '.' + evalLevelToken + 'Aligned'
        phonemesAlignedSuffix = '.phonemesAligned'
    return tokenAlignedSuffix, phonemesAlignedSuffix

def visualiseInPraat(URIrecordingNoExt,  withDuration, detectedFileName, detectedWordList = [], grTruthDurationWordList=[]):
    ### OPTIONAL############# : PRAAT
    pathToAudioFile = URIrecordingNoExt + '.wav'
    URIGrTruth = URIrecordingNoExt + ANNOTATION_EXT
    
    AlignedSuffix, phonemesAlignedSuffix = determineSuffix
    
# gr truth
# TODO: what to do with detection.
#     if grTruthDurationWordList != None and grTruthDurationWordList != []:
#         grTruthDurationfileExtension = '.grTruthDuration'
#         
#         
#         tokenList2TextGrid(tokenAlignedfileName, URIGrTruth)

# detected
    if detectedWordList != None and detectedWordList != []:
        if not withDuration and os.path.isfile(detectedWordList):
            alignedResultPath, fileNameWordAnno = addAlignmentResultToTextGridFIle(detectedWordList, URIGrTruth, wordsAlignedSuffix, phonemesAlignedSuffix)
        else:
            tokenList2TextGrid(detectedFileName, URIGrTruth)
         
        # TODO: add phone-level for detected
        

# open final TextGrid in Praat 
#     openTextGridInPraat(alignedResultPath, fileNameWordAnno, pathToAudioFile)


def tokenList2TextGrid(tokenAlignedfileName, URIGrTruthTextGrid):
    

     
    if os.path.isfile(URIGrTruthTextGrid):
         alignedResultPath, fileNameWordAnno = _alignmentResult2TextGrid(URIGrTruthTextGrid, tokenAlignedfileName) 
    else:
#  if no Textgrid groundTruthAnnotation present : open with Praat
        tab2PraatAndOpenWithPRaat(['dummy', tokenAlignedfileName] )
    

def plotStuff():
    # In[14]:
    
    #x - alpha
    alphas = np.arange(0.81,1,0.01)
    
    
    
    #errors for olmaz ilaç
    errorMeans = [ 2.13, 2.13, 2.03, 1.65, 1.44,1.34, 1.3, 1.07, 1.07, 1.06, 1.07, 0.9, 0.9, 0.89, 0.63, 0.13, 0.13, 0.13, 0.12 ]
    errorStDev = [2.18,  2.18, 2.22, 2.13, 2.09, 2.12, 2.14, 1.86, 1.86, 1.86, 1.87, 1.86, 1.85,1.85,  1.75, 0.17, 0.16, 0.17, 0.15]
    
    
    
    # In[15]:
    
    len(alphas)
    
    
    # In[ ]:
    
    
    plt.plot(alphas,errorMeans, 'r^', alphas, errorStDev, 'bs' )
    plt.show()
    
def plotScoreDevs():
    import matplotlib.pyplot as pyplot

    scoreDev  = [0.35, 
    0.45, 
    0.56, 
    0.63, 
    0.65, 
    0.83, 
    0.91, 
    1.01, 
    1.33]
    
    
    
    noDurationError = [
    
    0.64,
    0.41,
    0.93,
    1.83,
    0.94,
    2.17,
    1.09,
    0.78,
    1.49
    
    
    ]
    
    durationError =  [
    0.26,
    0.47,
    0.63,
    0.45,
    0.78,
    0.92,
    0.81,
    1.1,
    1.9
    ]
    
    
    
    pyplot.scatter(scoreDev,noDurationError, color='blue')
    
    pyplot.scatter(scoreDev,durationError, color='red')


