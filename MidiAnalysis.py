from music21 import *

#Following code taken from https://www.kaggle.com/code/wfaria/midi-music-data-extraction-using-music21

def open_midi(midi_path, remove_drums):
    # There is an one-line method to read MIDIs
    # but to remove the drums we need to manipulate some
    # low level MIDI events.
    mf = midi.MidiFile()
    mf.open(midi_path)
    mf.read()
    mf.close()
    if (remove_drums):
        for i in range(len(mf.tracks)):
            mf.tracks[i].events = [ev for ev in mf.tracks[i].events if ev.channel != 10]          

    return midi.translate.midiFileToStream(mf)

TestFile = open_midi("TestMidis/NoSurprises.mid", False)

def list_instruments(midi):
    partStream = midi.parts.stream()
    print("List of instruments found on MIDI file:")
    for p in partStream:
        aux = p
        print (p.partName)

def extract_notes(midi_part):
    parent_element = []
    ret = []
    for nt in midi_part.flat.notes:        
        if isinstance(nt, note.Note):
            ret.append(max(0.0, nt.pitch.ps))
            parent_element.append(nt)
        elif isinstance(nt, chord.Chord):
            for pitch in nt.pitches:
                ret.append(max(0.0, pitch.ps))
                parent_element.append(nt)
    
    return ret, parent_element

temp_midi_chords = open_midi("TestMidis/TestMidi.mid", False).chordify()
temp_midi = stream.Score()
temp_midi.insert(0, temp_midi_chords)

def note_count(measure, count_dict):
    bass_note = None
    for chord in measure.recurse().getElementsByClass('Chord'):
        # All notes have the same length of its chord parent.
        note_length = chord.quarterLength
        for note in chord.pitches:          
            # If note is "C5", note.name is "C". We use "C5"
            # style to be able to detect more precise inversions.
            note_name = str(note) 
            if (bass_note is None or bass_note.ps > note.ps):
                bass_note = note
                
            if note_name in count_dict:
                count_dict[note_name] += note_length
            else:
                count_dict[note_name] = note_length
        
    return bass_note

def simplify_roman_name(roman_numeral):
    # Chords can get nasty names as "bII#86#6#5",
    # in this method we try to simplify names, even if it ends in
    # a different chord to reduce the chord vocabulary and display
    # chord function clearer.
    ret = roman_numeral.romanNumeral
    inversion_name = None
    inversion = roman_numeral.inversion()
    
    # Checking valid inversions.
    if ((roman_numeral.isTriad() and inversion < 3) or
            (inversion < 4 and
                 (roman_numeral.seventh is not None or roman_numeral.isSeventh()))):
        inversion_name = roman_numeral.inversionName()
        
    if (inversion_name is not None):
        ret = ret + str(inversion_name)
        
    elif (roman_numeral.isDominantSeventh()): ret = ret + "M7"
    elif (roman_numeral.isDiminishedSeventh()): ret = ret + "o7"
    return ret

def harmonic_reduction(midi_file):
    ret = []
    temp_midi = stream.Score()
    temp_midi_chords = midi_file.chordify()
    temp_midi.insert(0, temp_midi_chords)    
    music_key = temp_midi.analyze('key')
    max_notes_per_chord = 4   
    for m in temp_midi_chords.measures(0, None): # None = get all measures.
        if (type(m) != stream.Measure):
            continue
        
        # Here we count all notes length in each measure,
        # get the most frequent ones and try to create a chord with them.
        count_dict = dict()
        bass_note = note_count(m, count_dict)
        if (len(count_dict) < 1):
            ret.append("-") # Empty measure
            continue
        
        sorted_items = sorted(count_dict.items(), key=lambda x:x[1])
        sorted_notes = [item[0] for item in sorted_items[-max_notes_per_chord:]]
        measure_chord = chord.Chord(sorted_notes)
        
        # Convert the chord to the functional roman representation
        # to make its information independent of the music key.
        roman_numeral = roman.romanNumeralFromChord(measure_chord, music_key)
        ret.append(simplify_roman_name(roman_numeral))
        
    return ret

#Following code written by Jacob Reed

chords = harmonic_reduction(open_midi("TestMidis/NoSurprises.mid", True))

def remove_inversion(chords):
    returnChords = []
    
    for i in range(len(chords)):
        tempChord = chords[i]
        
        if "2" in tempChord:
            tempChord = tempChord.replace("2", "")
            
        if "3" in tempChord:
            tempChord = tempChord.replace("3", "")
            
        if "4" in tempChord:
            tempChord = tempChord.replace("4", "")      
              
        if "5" in tempChord:
            tempChord = tempChord.replace("5", "")
                        
        if "6" in tempChord:
            tempChord = tempChord.replace("6", "")
        
        returnChords.append(tempChord)
          
    return returnChords

def check_for_repetition(chords):
    for i in range(len(chords)):
        if chords[i] > 1:
            return True
    return False

def find_common_progressions(chordDict):
    keyList = []
    chordsList = []
    
    for i in range(len(chordDict["Number"])):
        if chordDict["Number"][i] == max(chordDict["Number"]):
            keyList.append(i)
            
    for x in range(len(keyList)):
        chordsList.append(chordDict["Progression"][keyList[x]])
        
    return chordsList

def check_for_progressions(chords):
    chords = remove_inversion(chords)
    chordDict = {"Progression": [], "Number": []};
    chordDict["Number"].append(2)
    DictList = []
    
    for x in range(len(chords)):
        DictList.append({"Progression": [], "Number": []})

    DictList[0]["Number"].append(2)
    count = 0
    progression = ""
    
    while(check_for_repetition(DictList[count]["Number"])):
        count = count + 1
        for i in range(len(chords)-count):
            for x in range(count):
                if (i+x) >= len(chords):
                    break
                else:
                    progression = progression + " " +chords[i+x]
            
            if progression in DictList[count]["Progression"]:
                DictList[count]["Number"][DictList[count]["Progression"].index(progression)] = DictList[count]["Number"][DictList[count]["Progression"].index(progression)] + 1
                progression = ""
            else:
                DictList[count]["Progression"].append(progression)
                DictList[count]["Number"].append(1)
                progression = ""
         
    #print("Most Common Progressions:")
    return find_common_progressions(DictList[count-1])


#print(chords)    
print(check_for_progressions(chords))
            