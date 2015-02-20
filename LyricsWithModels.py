'''
Created on Oct 27, 2014

@author: joro
'''
from Lyrics import Lyrics
import os
import sys
from StateWithDur import StateWithDur
from htk_converter import HtkConverter
from Decoder import logger
from Constants import NUM_FRAMES_PERSECOND, AVRG_TIME_SIL, MAX_TIME_SIL

parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0]) ), os.path.pardir)) 

# htkModelParser = os.path.join(parentDir, 'htk2s3')
# sys.path.append(htkModelParser)



class LyricsWithModels(Lyrics):
    '''
    lyrics with each Phoneme having a link to a model of class type htkModel from htkModelParser
    '''


    def __init__(self, lyrics, htkParser, ONLY_MIDDLE_STATE  ):
        '''
        being  linked to models, allows expansion to network of states 
        '''
        Lyrics.__init__(self, lyrics.listWords)
        
        self._linkToModels(htkParser)
        
        # list of class type StateWithDur
        self.statesNetwork = []
        
        if ONLY_MIDDLE_STATE=='True':
            ONLY_MIDDLE_STATE  = True
        elif ONLY_MIDDLE_STATE=='False':
            ONLY_MIDDLE_STATE  = False
        else:
            sys.exit("param ONLY_MIDDLE_STATE ={}. ONly True/False expected".format( ONLY_MIDDLE_STATE))
        
        self.ONLY_MIDDLE_STATE = ONLY_MIDDLE_STATE
        
        if ONLY_MIDDLE_STATE:
            self._phonemes2stateNetworkOnlyMiddle()
        else:
            self._phonemes2stateNetwork()
#             self._phonemes2stateNetworkWeights()

        self.duratioInFramesSet = False

        
    def _linkToModels(self, htkParser):
        '''
        load links to trained models   
        '''
        # take only middle state of sil model: 
        for currHmmModel in htkParser.hmms:
            if currHmmModel.name == 'sil' and not len(currHmmModel.states)==1 :
                middleState = currHmmModel.states[1]
                currHmmModel.states = []
                currHmmModel.states.append(middleState) 
                
                
        
        # FIXME: DO A MORE OPTIMAL WAY like ismember()
        for phonemeFromTranscript in    self.phonemesNetwork:
            for currHmmModel in htkParser.hmms:
                if currHmmModel.name == phonemeFromTranscript.ID:
                    
                    phonemeFromTranscript.setHTKModel(currHmmModel) 
            
#         for phonemeFromTranscript in    self.phonemesNetwork:
#             phonemeFromTranscript.htkModel.display()
    #         (numState, state )  = phonemeFromTranscript.htkModel.states[1]
    #         state.display()
        ###### 
        
    def _phonemes2stateNetwork(self):
        '''
        expand to self.statesNetwork. 
        each state gets 1/n-th of total num of states. 
        '''
        
        self.statesNetwork = []
        stateCount = 0
        
        for phoneme in self.phonemesNetwork:
            
            phoneme.setNumFirstState(stateCount)
            # update state counter
            currStateCount = len(phoneme.htkModel.states)
            stateCount += currStateCount
            
            # assign durations
            for (numState, state ) in phoneme.htkModel.states:
                 currStateWithDur = StateWithDur(state.mixtures)
                 
                 dur = float(phoneme.getDurationInMinUnit()) / float(currStateCount)
                 
                 currStateWithDur.setDurationInMinUnit( dur )
                 self.statesNetwork.append(currStateWithDur)
                 
    def _phonemes2stateNetworkWeights(self):
        '''
        expand to self.statesNetwork. 
        each state gets a part proportional to  the weighting probs
        '''
        
        self.statesNetwork = []
        stateCount = 0
        
        for phoneme in self.phonemesNetwork:
            
            phoneme.setNumFirstState(stateCount)
            # update
            currStateCount = len(phoneme.htkModel.states)
            stateCount += currStateCount
            
            
            currTransMatrix = phoneme.getTransMatrix()
            currTransMatrix = currTransMatrix[1:-1,1:-1]
            
            # sanity check
            if not currStateCount ==  currTransMatrix.shape[0]:
                sys.exit("Error on reading htk model: transMatrix for phoneme {} has not same num states as states ", phoneme.ID)
            
            waitProbs = []
            for currState in range(currStateCount):
                currWaitProb =  currTransMatrix[currState, currState]
                waitProbs.append(currWaitProb)
            
            statesList = phoneme.htkModel.states
            # assign durations
            for  i, (numState, state ) in enumerate(statesList):
                 currStateWithDur = StateWithDur(state.mixtures)
                 
                 # normalize to sum to one
                 weigthState = float(waitProbs[i]) / float(sum(waitProbs))
                 dur = float(phoneme.getDurationInMinUnit()) * float(weigthState)
                 
                 currStateWithDur.setDurationInMinUnit( dur )
                 self.statesNetwork.append(currStateWithDur)
        
        

                 
               
    def _phonemes2stateNetworkOnlyMiddle(self):
        '''
        expand to self.statesNetwork . TAKE ONLY middle state for now
        '''
        
        self.statesNetwork = []
        stateCount = 0
        
        for phoneme in self.phonemesNetwork:
            
            phoneme.setNumFirstState(stateCount)
            # update
            stateCount += 1
            
        
            if len( phoneme.htkModel.states) == 1:
                (numState, state ) = phoneme.htkModel.states[0]
            elif len( phoneme.htkModel.states) == 3:             
                (numState, state ) = phoneme.htkModel.states[1]
            else:
                sys.exit("not implemented. only 3 or 1 state per phoneme supported")
            
            currStateWithDur = StateWithDur(state.mixtures)
            currStateWithDur.setDurationInMinUnit(phoneme.getDurationInMinUnit())
            
            self.statesNetwork.append(currStateWithDur)
    
    def printWordsAndStatesAndDurations(self, resultPath):
        '''
        debug word begining states
        '''
        
        for word_ in self.listWords:
            print word_ , ":" 
            for syllable_ in word_.syllables:
                for phoneme_ in syllable_.phonemes:
                    print "\t phoneme: " , phoneme_
                    countPhonemeFirstState =  phoneme_.numFirstState

                    for nextState in range(phoneme_.getNumStates()):
                        print "\t\t state: {} duration (in Frames): {} DURATION RESULT: {}, t_end: {}".format(countPhonemeFirstState + nextState, 
                                                                                                self.statesNetwork[countPhonemeFirstState + nextState].durationInFrames,
                                                                                                 resultPath.durations[countPhonemeFirstState + nextState], 
                                                                                                 resultPath.endingTimes[countPhonemeFirstState + nextState])

                    

                
                
    def duration2numFrameDuration(self, observationFeatures, URI_recording_noExt):
        '''
        get relative tempo (numFramesPerMinUnit) for given audio chunk
        and
        setDuration HowManyFrames for each state in statesNetwork
        '''
        # TODO: read from score
#         self.bpm = 60
#         durationMinUnit = (1. / (self.bpm/60) ) * (1. / MINIMAL_DURATION_UNIT) 
#         numFramesPerMinUnit = NUM_FRAMES_PERSECOND * durationMinUnit
        totalScoreDur = self.getTotalDuration()
        numFramesPerMinUnit   = float(len(observationFeatures) - 2 * AVRG_TIME_SIL * NUM_FRAMES_PERSECOND) / float(totalScoreDur)
#         numFramesPerMinUnit   = float(len(observationFeatures)) / float(totalScoreDur)

        
        # DEBUG: hardcoded read from groundTruth for kimseye
        # numFramesPerMinUnit = 3.67
        
        logger.debug("numFramesPerMinUnit = {} for audiochunk {} ".format( numFramesPerMinUnit, URI_recording_noExt))
        
        for  i, stateWithDur_ in enumerate (self.statesNetwork):

        # HARD CODE 1st and last state are silence
            if i == 0 or i == len(self.statesNetwork) - 1:
                durINFramesSIL = MAX_TIME_SIL*NUM_FRAMES_PERSECOND
                stateWithDur_.setDurationInFrames(durINFramesSIL)   
                
            else:
                # numFrames per phoneme
                numFramesPerState = round(float(stateWithDur_.duration) * numFramesPerMinUnit)
                stateWithDur_.setDurationInFrames(numFramesPerState)
        
        self.duratioInFramesSet = True
            
    
    def getDurationInFramesList(self):
        '''
        get Duration list (in NumFrames)
        '''
        numFramesDurationsList = []
        
        if not self.duratioInFramesSet:
            logger.warn("no duration in frames set. Please call first duration2numFrameDuration()")
            return numFramesDurationsList
        
        
        for  i, stateWithDur_ in enumerate (self.statesNetwork):
            numFramesDurationsList.append(stateWithDur_.getDurationInFrames()) 
        
        return numFramesDurationsList
        
        
        
    def printStates(self):
        '''
        debug: print states 
        '''
        
        
        for i, state_ in enumerate(self.statesNetwork):
                print "{} : {}".format(i, state_.display())
