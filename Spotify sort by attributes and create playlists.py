#!/usr/bin/env python
# coding: utf-8

# get token from
# https://developer.spotify.com/console/post-playlist-tracks/

# In[12]:


#################################
######### Change these: #########
#################################
TOKEN = 'BQBD2aW8VW6FogsU28QtFi8AjysMI1Y3md4mwa_ckpYnZgwurHjAbwVT0LI7P-VlGyaqxToiH9q7ucn7SgoI6EdTp-oGJ6x3UMz38KNRY1u_xL4SZSvT765SYSuWecVwx_jjvAW2ADQBWflZ35sHN-buIhRFG8L2vEqDZ-F9h0TlbnU4GMc_wevejnzQYnryYYhf5GN_Hd_aQLCkuryL5W4dcfH0S1t0Aos9QcSTsFNX7zl3oBgdPjRBOIyEgcv4iQILoB2PoOaGGJ00'
USER = 'jae94lee' #replace with your own spotify user id


import json
import requests
from math import ceil
import pandas as pd
from pandas.io.json import json_normalize
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
from datetime import datetime
pd.set_option('display.max_columns', None)

#authentification
cid ="39bc11236f6a4bd79c9eadcdbce37c4e" 
secret = "ac238b14eeb74bcd9e12947759c4eaab"

client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

headers = {'Authorization': "Bearer {}".format(TOKEN)}


# In[2]:


###########################################
############# HELER FUNCTIONS #############
###########################################

######### Get playlists ##############
def get_playlists():
    try:
        #50 is the max
        r5 = requests.get("https://api.spotify.com/v1/users/" + USER + "/playlists?offset=1&limit=50", headers=headers)
    except:
        pass
    
    pl = json.loads(r5.text)
    playlists_id_list = []    
    for i in range (0,50):
        playlists = pl['items'][i]['id']
        playlists_id_list.append(playlists)
        
    playlists_id_list_new = ','.join(str(i) for i in playlists_id_list)
    return playlists_id_list


############ Get audio features of each track id ##############
def get_audio_features(song_id_list):
    audio_features_url = f"https://api.spotify.com/v1/audio-features?ids="

    try:
        r2 = requests.get(audio_features_url + song_id_list, headers=headers)
    except:
        pass

    audio_features = json.loads(r2.text)['audio_features']
    audio_features_removed_none = [item for item in audio_features if item != None]
    x = pd.DataFrame.from_records(audio_features_removed_none)
    return x


############ Get Time and Key Signatures and mode ##############
def get_key_and_time_signature(song_id_list):
    
    #pitch class dict
    pitch_class = list(range(0,12))
    tone = ['C','C#','D','Eb','E','F','F#','G','G#','A','Bb','B']
    pitch_class_dict = {pitch_class[i]:tone[i] for i in range(len(pitch_class))}

    #mode dict
    mode_dict = {0:'minor', 1:'major', -1:'no_result'}

    features_df = get_audio_features(song_id_list)
    kts_df = features_df[['id', 'key', 'mode', 'time_signature']]  
    kts_df['key'] = kts_df['key'].replace(pitch_class_dict)
    kts_df['mode'] = kts_df['mode'].replace(mode_dict)
    kts_df.set_index('id')
    return kts_df


########## Get playlist's track ids ##############
def get_playlist_tracks(playlist_id):
    playlist_tracks_url = f"https://api.spotify.com/v1/playlists/"

    try:
        r3 = requests.get(playlist_tracks_url + playlist_id + f"/tracks", headers=headers)
    except:
        pass
    playlist_tracks = json.loads(r3.text)
    pt = playlist_tracks['items']
    pt_df =  pd.json_normalize(pt)
    
    #get artists and id
    artist_list = []
    song_id_list = []
    for i in range(0, len(pt)):
        song = pt[i]['track']
        if song is None:
            pass
            
        else:
            artist = song['artists'][0]['name']
            artist_list.append(artist)
            song_id = song['id']
            song_id_list.append(song_id)

    artists_and_id = pd.DataFrame()
    artists_and_id['id'] = song_id_list
    artists_and_id['artist'] = artist_list
    artists_and_id.set_index('id', inplace=True) 
        
    #get name and id
    name_and_id = pt_df[['track.id','track.name']]
    name_and_id.rename(columns={"track.id": "id", "track.name": "name"}, inplace=True)
    name_and_id.set_index('id', inplace=True)
    
    tracks_id_list = [] 
    for i in range(0, len(name_and_id)):
        tracks = pt[i]['track']
        if tracks is None:
            pass
        else:
            new = tracks['id']
            tracks_id_list.append(new)

    tracks_id_list_new = ','.join(str(i) for i in tracks_id_list)
    
    #get audio features of each track id
    x = get_key_and_time_signature(tracks_id_list_new)
    y = x.set_index('id')
    
    #combine audio features with name/artist/id    
    nameartist = name_and_id.join(artists_and_id)
    final = nameartist.join(y)
    return final


# In[3]:


#####################################
################ RUN ################
#####################################

#get the playlist ids
playlists_id_list = get_playlists()

#for each playlist, make a small dataframe and add to agg_df
agg_df = pd.DataFrame()
for count, playlist_id in enumerate(playlists_id_list):
    one_playlist_df = get_playlist_tracks(playlist_id)   
    agg_df = agg_df.append(one_playlist_df)

agg_df.head()


# In[4]:


agg_df.shape


# In[5]:


agg_df['time_signature'].value_counts()


# In[6]:


#############################################################
######################## Export to csv ######################
#############################################################
agg_df.to_csv('spotify_key_time_signature_output.csv')


# In[7]:


#############################################################
############ Manipulation. Do whatever you want #############
#############################################################

#Bb minor key only
dff = agg_df[(agg_df['key'] == 'Bb') & (agg_df['mode'] == 'minor')]
dff.head()


# In[15]:


##############################################################
############### Create Playlist from track ids ###############
##############################################################

#First, create a playlist on spotify and get its id through its link. (Can automate this in the future too)
PLAYLIST_ID = '5xyc9ZHEHunDLuL6aJyQa5'


pre_uris = f"https://api.spotify.com/v1/playlists/"
headers = {'Authorization': "Bearer {}".format(TOKEN)}

# get track ids in batches of 10 to avoid 414 response
ids = dff.index.tolist()
new_ids = ["spotify:track:" + item for item in ids]
length = len(new_ids)
i = 0
while i+10 < length:
    ids_10 = ','.join(str(x) for x in new_ids[i:i+10])

    uris = pre_uris + PLAYLIST_ID + '/tracks?uris=' + ids_10
    print(uris)
    try:   
        response = requests.post(uris, headers=headers)
        print(response)
    except:
        pass
    i = i+10
  
