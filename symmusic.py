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
from mutagen.flac import FLAC  
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis 
#from unidecode import unidecode -- will simplify UTF to ASCII

###
# Globals
###

tagdict = {
    '%g' : 'genre',
    '%a' : 'artist',
    '%l' : 'album',
    '%t' : 'title',
    '%n' : 'tracknumber',
    '%y' : 'year',
    }
    
formats = [ 'mp3', 'flac', 'ogg' ]

###
# Functiions
###

def parseArgs():
  #TODO: 
  #   * add format options
  #   * add seperator options
  ap = (argparse.ArgumentParser(
    description='Create directory structure based on audio tags.'))
  ap.add_argument('--dn',nargs='+',required=True,choices=tagdict, \
                          help='IN ORDER! Directory level tags')
  ap.add_argument('--fn',nargs='+',required=True,choices=tagdict, \
                          help='IN ORDER! Tags for filenames')
  ap.add_argument('--formats',nargs='+',default=formats,choices=formats, \
                          help='Formats to search for')
  ap.add_argument('-s', '--src', default=os.getcwd(),help='Source directory.')
  ap.add_argument('-d','--dst', required=True,help='Destination path') 
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
  print "Number of %s found: %d" % (pattern,len(musiclist))
  return musiclist

def getTag(f,fun,tagname):
  """ Get an mp3 tag, fail without fanfare
  """
  try:
    tags = fun(f)
  except ValueError:
    tags = 'Unknown'
  if tags.has_key(tagname):
    try:
      tag = tags[tagname][0]
      if tag:
        cleaned = tag.encode('UTF-8') #unidecode()?
        slashproofed = re.sub(r"/","-",cleaned) #Hack....
        return slashproofed
      else:
        return 'Unknown'
    except IndexError:
      pass
  else:
      return 'Unknown'
  
def getTagList(f,fun,ext,tagnames):
  """ Get multiple tags for a file, based on a given list
  """
  tags = []
  for tagname in tagnames:
    tag = getTag(f,fun,tagname)
    if tagname is 'album':
      tag = tag + ' [' + ext + ']'
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
  
def enchilada(encoding,dirs,names,dst):
  #Dumb count of succesful mp3 symbolic links
  made = 0 
  for f in encoding[0]:
    try:
      dirtags = getTagList(f,encoding[1],encoding[2],dirs)
      nametags = getTagList(f,encoding[1],encoding[2],names)
     # print dirtags, nametags
      makeDirHeir(dirtags,nametags,encoding[2],f,dst)
      made += 1
    except AttributeError or UnboundLocalError:
      pass
  print "Succesful %s makes: %i" % (encoding[2],made)

###
# Main
###

def main():

  #Getting the arguments
  args = parseArgs()
  src = os.path.abspath(args.src)     #Source directory
  dst = os.path.abspath(args.dst)     #Destination
  dirs = getDict(args.dn,tagdict)     #Directory name tags
  names = getDict(args.fn,tagdict)    #Filename tags

  #List of files
  # TODO: refactor to make formats a list
  mp3s = getMusic(src,".mp3")
  flacs = getMusic(src,".flac")
  oggs = getMusic(src,".ogg")

  #Tuple makin'
  mp3 = mp3s, EasyID3, '.mp3'
  flac = flacs, FLAC, '.flac'
  ogg = oggs, OggVorbis, '.ogg'

  #The big creation
  enchilada(mp3,dirs,names,dst)
  enchilada(flac,dirs,names,dst)
  enchilada(ogg,dirs,names,dst)
  
if __name__ == '__main__':
    main()


