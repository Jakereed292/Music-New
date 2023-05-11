import os
import json
import sqlite3
from MidiAnalysis import *

#Following code taken from http://millionsongdataset.com/sites/default/files/tutorial1.pdf

DATA_PATH = 'data'
RESULTS_PATH = 'C:/Users/JacobPc.DESKTOP-P3BHUK1/Vscode/MusicProject'
SCORE_FILE = os.path.join(RESULTS_PATH, 'match_scores.json')

def msd_id_to_dirs(msd_id):
    """Given an MSD ID, generate the path prefix.
    E.g. TRABCD12345678 -> A/B/C/TRABCD12345678"""
    return os.path.join(msd_id[2], msd_id[3], msd_id[4], msd_id)

with open(SCORE_FILE) as f:
    scores = json.load(f)
msd_id = ""

#Following code written by Jacob Reed
 
dbLocation = "C:/Users/JacobPc.DESKTOP-P3BHUK1/Vscode/MusicProject/lmd/lmd_aligned" 

#range(len(list(scores.keys()))):
progressionList = []
for i in range(10): 
    midiDict = {"ID": [], "Score": []};
    msd_id = list(scores.keys())[i]
    
    for midi_md5, score in scores[msd_id].items():
        midiDict["ID"].append(midi_md5)
        midiDict["Score"].append(score)
    
    index = midiDict["Score"].index(max(midiDict['Score']))
    chords = check_for_progressions(harmonic_reduction(open_midi(os.path.join(dbLocation,msd_id_to_dirs(list(scores.keys())[i]),midiDict['ID'][index] + ".mid"), True)))
    progressionList.append((msd_id,str(chords)))

print(progressionList)

conn = sqlite3.connect('track_metadata.db')
c = conn.cursor()

c.execute("DROP TABLE progressions")
c.execute("""CREATE TABLE progressions(
            mid text,
            progression text)         
        """)
c.executemany("INSERT INTO progressions VALUES (?,?)", progressionList)
c.execute("""SELECT track_id,title,artist_name,progression FROM progressions
             INNER JOIN songs on track_id = mid""")

rows = c.fetchall()
for row in rows:
    print(row)

conn.commit()
conn.close()