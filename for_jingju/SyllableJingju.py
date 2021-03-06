'''
Created on Oct 8, 2014

@author: joro
'''
import os
import sys
import sys

from numpy.ma.core import ceil
from PhonetizerDict import loadXSAMPAPhonetizers, toXSAMPAPhonemes,\
    tokenizePhonemes


parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__) ), os.path.pardir)) 

pathHMMDuration = os.path.join(parentDir, 'AlignmentDuration')
if pathHMMDuration not in sys.path:
    sys.path.append(pathHMMDuration)


from PhonemeJingju import PhonemeJingju
from align.Phonetizer import Phonetizer
from align._SyllableBase import _SyllableBase


from align.ParametersAlgo import ParametersAlgo
import logging 

logger = logging.getLogger(__name__)

class SyllableJingju(_SyllableBase):
        ''' syllables class for each chinse/for_jingju phoneme (using phonemeSet mandarin from Weng Lei)
        BUT not meant to be used alone, instead Syllable is a part of a Word class
        '''
        def __init__(self, text, noteNum):
            _SyllableBase.__init__(self, text, noteNum)
           
#         def get_Duration(self):
#             return self.duration    
        
            self.durationPhonemes = None
        





        def expandToPhonemes(self):
            '''
            expand PINYIN characters to XAMPA phonemes. 
            '''
            
            ######################
            ### pinyin to mandarin phonemeSet
            if not Phonetizer.phoneticDict:
                sys.exit("Phonetizer.phonetic Dict not defined. do Phonetizer.initPhoneticDict at beginning of all code")   
            
            self.phonemes = []    

            #  notes for instrument
            if self.text == 'REST' or self.text == '':
                # TODO: replace with other models_makam instead of silence
                silPhoneme = PhonemeJingju('sil')
#                 silPhoneme.durationInNumFrames = 100
                self.phonemes.append(silPhoneme)
                # TODO: does sp at end of sp make sence? 
#                 self.phonemes.append(PhonemeJingju('sp'))
                self.hasShortPauseAtEnd = False
                return
            
           
            
            if self.text in Phonetizer.phoneticDict:
                xsampaPhonemesGrouped = Phonetizer.phoneticDict[self.text]
            else: # add pinyin syllalble to phonetic dict
                logger.warning(" syllable in PINYIN {} not in dict".format(self.text))
                consonants, consonants2, vocals, specials = loadXSAMPAPhonetizers()
                xsampaPhonemesGrouped = toXSAMPAPhonemes(self.text, consonants, consonants2, vocals, specials)
                
                Phonetizer.phoneticDict[self.text] = xsampaPhonemesGrouped # add syllable to dict
            
            xsampaPhonemes = tokenizePhonemes(xsampaPhonemesGrouped)

              
            ####################
            #### create Phonemes objects form phoneme IDs
            
            self._createPhonemeClasses(xsampaPhonemes)
        
        
        
        def _createPhonemeClasses(self, phonemesList):
            '''
            utility
            '''
            for phonemeID in phonemesList:
                self.phonemes.append(PhonemeJingju(phonemeID))
            
            if self.hasShortPauseAtEnd:
                self.phonemes.append(PhonemeJingju('sp'))
                
                
                
        
        def calcPhonemeDurations(self):
            '''
            rule-based assignment of durations using Initial-Middle-final rules
            all consonant durations set to CONSONANT_DURATION 
                        '''
            cofficinetTempo = 1
            
            if self.phonemes is None:
                self.expandToPhonemes()
            
            if self.getNumPhonemes() == 0:
                sys.exit("syllable with no phonemes!")
                return
            
            
            #copy to local var
            consonant_duration = ParametersAlgo.CONSONANT_DURATION
            
            # Workaraound: reduce consonant durationInMinUnit for syllables with very short note value. 
            while (self.getNumPhonemes() - 1) * consonant_duration >= self.durationInNumFrames:
                logger.warning("Syllable {} has very short durationInMinUnit: {} . reducing the fixed durationInMinUnit of consonants".format(self.text, self.durationInMinUnit) )
                consonant_duration /=2
            
            #################
            ## assign durations 
            #############
            
          
            initPhoneme = self.phonemes[0]
            finalPhoneme = self.phonemes[-1]
            
#                               
            if not initPhoneme.isVowel():  # initial is consonant
                initPhoneme.durationInNumFrames = consonant_duration

                if not finalPhoneme.isVowel():                 # final is consonant
                    finalPhoneme.durationInNumFrames = consonant_duration
                    # assign middle
                    for currPhoneme in self.phonemes[1:-1]:
                        currPhoneme.durationInNumFrames = (self.durationInNumFrames - 2 * consonant_duration) / len(self.phonemes[1:-1])
                        
                else:   # final is vowel
                    dur = (self.durationInNumFrames - float(consonant_duration) ) / len(self.phonemes[1:])
                    ceilDur = int(ceil(dur))
                    # assign middle
                    for currPhoneme in self.phonemes[1:-1]:
                        currPhoneme.durationInNumFrames = ceilDur
                    finalPhoneme.durationInNumFrames = self.durationInNumFrames - (len(self.phonemes[1:-1]) * ceilDur)
            
            else: # initial is vowel
                if not finalPhoneme.isVowel(): 
                    finalPhoneme.durationInNumFrames = consonant_duration
                    # assign middle
                    for currPhoneme in self.phonemes[:-1]:
                        currPhoneme.durationInNumFrames = (self.durationInNumFrames -   consonant_duration) / len(self.phonemes[:-1])
                else:   # final is vowel
                    # assign middle
                    for currPhoneme in self.phonemes:
                        currPhoneme.durationInNumFrames = self.durationInNumFrames / len(self.phonemes) 
     


       