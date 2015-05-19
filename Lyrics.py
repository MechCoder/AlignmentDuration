'''
Created on Oct 27, 2014

@author: joro
'''
from Phoneme import Phoneme


class Lyrics(object):
    '''
    Lyrics data structures
    appends sil at start and end of sequence

    '''


    def __init__(self, listWords):
        '''
        Word[]
        '''
        self.listWords = listWords
        '''
        Phoneme [] : list of phonemes
        '''
        self.phonemesNetwork =  []
        
        self._words2Phonemes()
        
    
    def _words2Phonemes(self):
        ''' convert list of words (Word []) to 
        @return: self.phonemesNetwork: 
        '''
      
#         TODO: set durationInMinUnit distribution type
        phonemeSil = Phoneme("sil"); 
        
        # does this matter when expo distribution?
        phonemeSil.setDurationInMinUnit('1')
        
#         self.phonemesNetwork.append(phonemeSil)
        
        # start word after sil phoneme
#         currNumPhoneme = 1
        
        for word_ in self.listWords:
            for syllable_ in word_.syllables:
                syllable_.expandToPhonemes()
                self.phonemesNetwork.extend(syllable_.getPhonemes() )
            
#             word_.setNumFirstPhoneme(currNumPhoneme)
            # update index
#             currNumPhoneme += word_.getNumPhonemes()
        
        phonemeSil2 = Phoneme("sil"); phonemeSil2.setDurationInMinUnit('1')
#         self.phonemesNetwork.append(phonemeSil2)
    
    def calcPhonemeDurs(self):
        '''
        distribute duraitions among phonemes within each syllable
        '''
        for word_ in self.listWords:
            for syllable in word_.syllables:
                syllable.calcPhonemeDurations()
                 
    
    def printSyllables(self):
        '''
        debug: print syllables 
        '''
        
        
        for word_ in self.listWords:
                for syll in word_.syllables:
                    print syll
                    
    def getTotalDuration(self):
        '''
        total durationInMinUnit of phonemes according to score. no pauses considered.
        '''
        totalDuration = 0    
        for word_ in self.listWords:
            for syllable_ in word_.syllables:
                totalDuration +=  int(syllable_.durationInMinUnit)
        return totalDuration
            
    
    def printPhonemeNetwork(self):
        '''
        debug: score-derived phoneme  durationInMinUnit 
        '''
               
        for i, phoneme in enumerate(self.phonemesNetwork):
            print "{}: {} {}".format(i, phoneme.ID, phoneme.durationInMinUnit)
#                         print "{}".format(phoneme.ID)

                 
    def __str__(self):
        lyricsStr = ''
        for word_ in self.listWords:
            lyricsStr += word_.__str__()
            lyricsStr += ' '
        return lyricsStr.rstrip().encode('utf-8','replace')
        
        