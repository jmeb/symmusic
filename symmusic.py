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
import argparse
import mutagen
#from mutagen.flac import FLAC  -- not yet implemented
from mutagen.easyid3 import EasyID3
#from mutagen.oggvorbis import OggVorbis -- no yet implemented
#from unidecode import unidecode -- will simplify UTF to ASCII

###
# Globals
###

tagdict = {
    'g' : 'genre',
    'a' : 'artist',
    'l' : 'album',
    't' : 'title',
    'n' : 'tracknumber',
    'g' : 'genre',
    }
    
###
# Functions
###
def parseArgs():
  ap = argparse.ArgumentParser(description='Create directory structure based on audio tags.')
  ap.add_argument('--dn',nargs='+',choices=tagdict,help='IN ORDER! Directory level tags')
  ap.add_argument('--fn',nargs='+',choices=tagdict,help='IN ORDER! Tags for filenames')
  ap.add_argument('-s', '--src', default=os.getcwd(),help='Source directory.')
  ap.add_argument('dst', help='Destination path') #Required at end
  return ap.parse_args()

def getDict(args,dictionary):
  tags = []
  for t in args:
    tags.append(dictionary[t])
  return tags

def getMusic(src,pattern):
  """ Get a list of music files with a particular file extension 
  """
  musiclist = []
  for root, dirs, files in os.walk(src):
    for fn in files:
      if fn.endswith(pattern):
        musiclist.append(os.path.join(root, fn))
  return musiclist

def getMP3Tag(f,tagname):
  """ Get an mp3 tag, fail without fanfare
  """
  try:
    tags = EasyID3(f)
  except ValueError:
    tags = 'None'
  if tags.has_key(tagname):
    try:
      tag = tags[tagname][0]
      if tag:
        cleaned = tag.encode('UTF-8') #unidecode()?
        slashproofed = re.sub(r"/","-",cleaned) #Hack....
        return slashproofed
      else:
        return ''
    except IndexError:
      pass
  else:
      return 'Unknown'
  
def getMP3Tags(f,tagnames):
  """ Get multiple tags for a file, based on a given list
  """
  tags = []
  for tagname in tagnames:
    tag = getMP3Tag(f,tagname)
    tags.append(tag)
  return tags

def makeDirHeir(dirs,nametags,ext,source,base):
  """ Make directory heirarch based on tag order
  """
  try:
    for tag in dirs:
      if os.path.exists(os.path.join(base,tag)) is False:
        os.makedirs(os.path.join(base,tag))
      base = os.path.join(base,tag)
    name = " - ".join(nametags) + ext
    os.symlink(source,os.path.join(base,name))
  except OSError or AttributeError:
    pass
  
def main():

  args = parseArgs()

  src = os.path.abspath(args.src)     #Source directory
  dst = os.path.abspath(args.dst)     #Destination
  dirs = getDict(args.dn,tagdict)     #Directory name tags
  names = getDict(args.fn,tagdict)    #Filename tags

  mp3s = getMusic(src,".mp3")

  print "Number of mp3's found: ",  len(mp3s)

  made = 0

  # Get tags, and make directory at same time for every mp3
  # This should be factored out into a function
  for f in mp3s:
    try:
      dirtags = getMP3Tags(f,dirs)
      nametags = getMP3Tags(f,names)
     # print dirtags, nametags
      makeDirHeir(dirtags,nametags,".mp3",f,dst)
      made += 1
    except AttributeError or UnboundLocalError:
      pass

  print "Number of mp3's written: ", made
  diff = len(mp3s) - made
  print "Number of mp3's without tags:", diff

if __name__ == '__main__':
    main()


