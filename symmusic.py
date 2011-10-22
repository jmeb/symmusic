#! /usr/bin/env python
#
# This program is free software.
# If it is ever distributed it is under a beerware license
#
#

###
# Imports
###

import sys
import os
import re
import mutagen
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis
from unidecode import unidecode

###
# Globals
###

dirs = ["artist","album"]   #List of tags for directory heirarchy
names = ["tracknumber","title"]           #Naming elements

###
# Functions
###

def getMusic(src,pattern):
  """ Get a list of music files with a particular file extension 
  """
  musiclist = []
  for root, dirs, files in os.walk(src):
    for fn in files:
      if fn.endswith(pattern):
        musiclist.append(os.path.join(root, fn))
  return musiclist

# Need to clean up tag output here to make path-able!!!
# somewhat done...problem in 10/12 track numbers
#     * 'Fixed' by subbing out / for -
def getMP3Tag(f,tagname):
  """ Get an mp3 tag, fail nicely
  """
  try:
    tags = EasyID3(f)
  except ValueError:
    return None
  if tags.has_key(tagname):
    tag = tags[tagname][0]
    if tag:
      cleaned = unidecode(tag.encode('UTF-8'))
      slashproofed = re.sub(r"/","-",cleaned) 
      return slashproofed
    else:
      return ''
  else:
      return ''
  
def getMP3Tags(f,tagnames):
  """ Get multiple tags for a file, based on a given list
  """
  tags = []
  for tagname in tagnames:
    tag = getMP3Tag(f,tagname)
    tags.append(tag)
  return tags

def makeDirHeir(dirs,nametags,source,base):
  """ Make directory heirarch based on tag order
  """
  try:
    for tag in dirs:
      if os.path.exists(os.path.join(base,tag)) is False:
        os.makedirs(os.path.join(base,tag))
      base = os.path.join(base,tag)
    name = " - ".join(nametags) 
    os.symlink(source,os.path.join(base,name))
  except OSError or AttributeError:
    pass

  
def main():

  # Dumb arg parsing, src and dst directories
  src = os.path.abspath(sys.argv[1])
  dst = os.path.abspath(sys.argv[2])

  # Get list of mp3s
  mp3s = getMusic(src,".mp3")

  print len(mp3s)

  # Get tags, and make directory at same time for every mp3
  for f in mp3s:
    dirtags = getMP3Tags(f,dirs)
    nametags = getMP3Tags(f,names)
    print dirtags, nametags
    makeDirHeir(dirtags,nametags,f,dst)

if __name__ == '__main__':
    main()


