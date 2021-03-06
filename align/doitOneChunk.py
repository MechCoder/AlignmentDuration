'''
Created on Oct 13, 2014

@author: joro
'''
import os
import numpy
import sys
from _LyricsWithModelsBase import _LyricsWithModelsBase
from numpy.core.arrayprint import set_printoptions
from Decoder import Decoder, logger
from LyricsParsing import expandlyrics2WordList, _constructTimeStampsForToken, testT
from Constants import NUM_FRAMES_PERSECOND, AUDIO_EXTENSION
from Phonetizer import Phonetizer
from docutils.parsers.rst.directives import path
from matplotlib.path import Path
from mhlib import PATH
from docutils.nodes import section
from MakamScore import loadMakamScore



# file parsing tools as external lib 
parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__) ), os.path.pardir)) 

# pathUtils = os.path.join(parentDir, 'utilsLyrics')
# sys.path.append(pathUtils )
from utilsLyrics.Utilz import writeListOfListToTextFile, writeListToTextFile,\
    getMeanAndStDevError, getSectionNumberFromName, readListOfListTextFile, readListTextFile, getMelodicStructFromName, tokenList2TabFile

# parser of htk-build speech models_makam
pathHtkModelParser = os.path.join(parentDir, 'pathHtkModelParser')
sys.path.append(pathHtkModelParser)
from htkparser.htk_converter import HtkConverter

# Alignment with HTK
pathAlignmentStep = os.path.join(parentDir, 'AlignmentStep')
if not pathAlignmentStep in sys.path:
    sys.path.append(pathAlignmentStep)
from Aligner import Aligner 

#  evaluation  
pathEvaluation = os.path.join(parentDir, 'AlignmentEvaluation')
if pathEvaluation not in sys.path:
    sys.path.append(pathEvaluation)
    

    
from hmm.Parameters import Parameters
from hmm.examples.tests import test_oracle

from WordLevelEvaluator import _evalAlignmentError, evalAlignmentError, tierAliases, determineSuffix
from AccuracyEvaluator import _evalAccuracy, evalAccuracy
from parse.TextGrid_Parsing import TextGrid2WordList

# from pymatbridge import Matlab

numpy.set_printoptions(threshold='nan')

currDir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) )
modelDIR = currDir + '/models_makam/'
HMM_LIST_URI = modelDIR + '/monophones0'
MODEL_URI = modelDIR + '/hmmdefs9gmm9iter'

ANNOTATION_EXT = '.TextGrid'    
AUDIO_EXT = '.wav'




def doitOneChunk(argv):
    
    if len(argv) != 8 and  len(argv) != 9 :
            print ("usage: {}  <pathToComposition> <URI_recording_no_ext> <withDuration=True> <withSynthesis> <ALPHA> <ONLY_MIDDLE_STATE> <evalLevel> <usePersistentFiles=True>".format(argv[0]) )
            sys.exit();
    
    
    URIrecordingNoExt = argv[2]
    whichSection, recordingWholeURI = getSectionNumberFromName(URIrecordingNoExt)

    pathToComposition = argv[1]
    withDuration = argv[3]
    if withDuration=='True':
        withDuration = True
    elif withDuration=='False':
        withDuration = False
    else: 
        sys.exit("withDuration can be only True or False")  
    
    withSynthesis = argv[4]
    if withSynthesis=='True':
        withSynthesis = True
    elif withSynthesis=='False':
        withSynthesis = False
    else: 
        sys.exit("withSynthesis can be only True or False")  
    
    
    ALPHA = float(argv[5])
    ONLY_MIDDLE_STATE = argv[6]
    
    evalLevel = tierAliases.words
    evalLevel = int(argv[7])
    
    deviationInSec = 0.1
    params = Parameters(ALPHA, ONLY_MIDDLE_STATE)
    
    usePersistentFiles = 'True'
    if len(argv) == 9:
        usePersistentFiles =  argv[8]
    
    
    set_printoptions(threshold='nan') 
    
    ################## load lyrics and models 
    htkParser = None
    if withDuration:
        htkParser = HtkConverter()
        htkParser.load(MODEL_URI, HMM_LIST_URI)
    
    alignmentErrors, correctDuration, totalDuration, correctDurationScoreDev = alignDependingOnWithDuration(URIrecordingNoExt, whichSection, pathToComposition, withDuration, withSynthesis, evalLevel, params, usePersistentFiles, htkParser)
        
    accuracy = correctDuration / totalDuration
    logger.info("accuracy: {:.2f}".format(accuracy))
    
    mean, stDev, median = getMeanAndStDevError(alignmentErrors)
    logger.info("mean : {} st dev: {} ".format( mean,stDev))


    


def alignDependingOnWithDuration(URIrecordingNoExt, sectionLink, pathToComposition, withDuration, withSynthesis, evalLevel, params, usePersistentFiles, htkParser):
    '''
    call alignment method depending on whether duration or htk  selected 
    '''
    #### 1) load lyrics
   
    makamScore = loadMakamScore(pathToComposition)
    
    lyrics = makamScore.getLyricsForSection(sectionLink.melodicStructure)
    
    lyricsStr = lyrics.__str__()
        
    if not lyricsStr or lyricsStr=='None' or  lyricsStr =='_SAZ_':
            logger.warn("skipping sectionLink {} with no lyrics ...".format(sectionLink.melodicStructure))
            return [], 'dummy', 0, 0, 0
    
    ##############
    ## reference duration
#     correctDurationScoreDev, totalDuration  = getReferenceDurations(URIrecordingNoExt, lyricsWithModels, evalLevel)
    correctDurationScoreDev = 0
    
    tokenLevelAlignedSuffix, phonemesAlignedSuffix = determineSuffix(withDuration, withSynthesis, evalLevel)
    alignmentErrors = []
    
    if withDuration:

        withOracle = 0
        oracleLyrics = 'dummy'
        detectedTokenList, detectedPath, maxPhiScore = alignOneChunk( lyrics, withSynthesis, withOracle, oracleLyrics, [], params.ALPHA,  usePersistentFiles, tokenLevelAlignedSuffix, URIrecordingNoExt, sectionLink, htkParser)
        logger.debug('maxPhiScore: ' + str(maxPhiScore) )

        correctDuration = 0
        totalDuration = 1
#         correctDuration, totalDuration = _evalAccuracy(URIrecordingNoExt + ANNOTATION_EXT, detectedTokenList, evalLevel )
#         detectedTokenList = test_oracle(URIrecordingNoExt, pathToComposition, whichSection)
            
    else:
        URIrecordingAnno = URIrecordingNoExt + ANNOTATION_EXT
        URIrecordingWav = URIrecordingNoExt + AUDIO_EXTENSION
        # new makamScore used
#         lyricsObj = loadLyrics(pathToComposition, whichSection)
#         lyrics = lyricsObj.__str__()
# #         in case  we are at no-lyrics sectionLink
#         if not lyrics or lyrics=='None' or  lyrics =='_SAZ_':
#             logger.warn("skipping sectionLink {} with no lyrics ...".format(whichSection))
#             return [], [], [], []
    
        outputHTKPhoneAlignedURI = Aligner.alignOnechunk(MODEL_URI, URIrecordingWav, lyricsStr, URIrecordingAnno, '/tmp/', withSynthesis)
        alignmentErrors = []
        alignmentErrors = evalAlignmentError(URIrecordingAnno, outputHTKPhoneAlignedURI, evalLevel)
        detectedTokenList = outputHTKPhoneAlignedURI
        
#         correctDuration, totalDuration = evalAccuracy(URIrecordingAnno, outputHTKPhoneAlignedURI, evalLevel)
        
     
    return alignmentErrors,  correctDuration, totalDuration, correctDurationScoreDev, maxPhiScore
    




def alignOneChunk(lyrics, withSynthesis, withOracle, lyricsWithModelsORacle, listNonVocalFragments, alpha, usePersistentFiles, tokenLevelAlignedSuffix,  URIrecordingNoExt, currSectionLink, htkParser):
    '''
    wrapper top-most logic method
    '''
    if withOracle:

        # synthesis not needed really in this setting. workaround because without synth takes whole recording  
        withSynthesis = 1
        
#     read from file result
    URIRecordingChunkResynthesizedNoExt =  URIrecordingNoExt + "_" + str(currSectionLink.beginTs) + '_' + str(currSectionLink.endTs)
    detectedAlignedfileName = URIRecordingChunkResynthesizedNoExt + tokenLevelAlignedSuffix
    if not os.path.isfile(detectedAlignedfileName):
        #     ###### extract audio features
        lyricsWithModels, obsFeatures, URIrecordingChunk = loadSmallAudioFragment(lyrics, 'dummyExtractedPitchList', URIrecordingNoExt, URIRecordingChunkResynthesizedNoExt, bool(withSynthesis), currSectionLink, htkParser)
            #     lyricsWithModels, observationFeatures = loadSmallAudioFragment(lyrics,  URIrecordingNoExt, withSynthesis, fromTs=-1, toTs=-1)
        
    # DEBUG: score-derived phoneme  durations
#     lyricsWithModels.printPhonemeNetwork()
#     lyricsWithModels.printWordsAndStates()
   
        decoder = Decoder(lyricsWithModels, URIRecordingChunkResynthesizedNoExt, alpha)
    #  TODO: DEBUG: do not load models
    # decoder = Decoder(lyrics, withModels=False, numStates=86)
    #################### decode
        if usePersistentFiles=='True':
            usePersistentFiles = True
        elif usePersistentFiles=='False':
            usePersistentFiles = False
        else: 
            sys.exit("usePersistentFiles can be only True or False") 
        
        if withOracle:
            detectedTokenList = decoder.decodeWithOracle(lyricsWithModelsORacle, URIRecordingChunkResynthesizedNoExt )
        else:
            detectedTokenList = decoder.decodeAudio(obsFeatures, listNonVocalFragments, usePersistentFiles)
        
        phiOptPath = decoder.path.phiOptPath
        detectedPath = decoder.path.pathRaw
        tokenList2TabFile(detectedTokenList, URIRecordingChunkResynthesizedNoExt, tokenLevelAlignedSuffix, currSectionLink.beginTs)
     
       
        
    ### VISUALIZE result 
#         decoder.lyricsWithModels.printWordsAndStatesAndDurations(decoder.path)
    
    else:   
            print "{}\n already exists. No decoding".format(detectedAlignedfileName)
            detectedTokenList = readListOfListTextFile(detectedAlignedfileName)
            if withOracle:
                outputURI = URIRecordingChunkResynthesizedNoExt + '.path_oracle'
            else:
                outputURI = URIRecordingChunkResynthesizedNoExt + '.path'
            
            detectedPath = readListTextFile(outputURI)
            
            # TODO: store persistently
            phiOptPath = 0
   

    return detectedTokenList, detectedPath, phiOptPath




    

def getReferenceDurations(URI_recording_noExt, lyricsWithModels, evalLevel):
        '''
        timestamps of words according to reference durations read from score. Used to obtain so called 'score-deviation' metric
        not used in decoding 
        '''
        
        
        annotationURI = URI_recording_noExt + ANNOTATION_EXT

        ##### get duration of initial silence 

        try:
            annotationTokenListA = TextGrid2WordList(annotationURI, evalLevel)     
            
            # just copy duration of silence in groundTruth 
            annoTsAndToken =  annotationTokenListA[0]
            if annoTsAndToken[2] != "" and not(annoTsAndToken[2].isspace()): # skip empty phrases
                    logger.warn("annotaiton {} starts with non-sil token ".format(annotationURI))
                    finalSilFram =  float(annoTsAndToken[0]) * NUM_FRAMES_PERSECOND
            else:
                finalSilFram = float(annoTsAndToken[1]) * NUM_FRAMES_PERSECOND
            
        
        except :
        # if no Gr Truth annotation file (or needed layer) present - take from model    
            finalSilFram = 0
            countFirstStateFirstWord = lyricsWithModels.listWords[0].syllables[0].phonemes[0].numFirstState
             
            for i in range(countFirstStateFirstWord):
                finalSilFram += lyricsWithModels.statesNetwork[i].getDurationInFrames()
        
            
        refTokenList = expandlyrics2WordList (lyricsWithModels, lyricsWithModels.statesNetwork, finalSilFram,  _constructTimeStampsForToken)
        grTruthDurationfileExtension = '.scoreDeviation'
        writeListOfListToTextFile(refTokenList, None , URI_recording_noExt + grTruthDurationfileExtension )
        
#     TODO: could be done easier with this code, and check last method in Word
#         refTokenList =    testT(lyricsWithModels)

        correctDuration, totalDuration = _evalAccuracy(annotationURI, refTokenList, evalLevel )

        return correctDuration, totalDuration



