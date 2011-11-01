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

###
# Globals
###

tagdict = {
    '%g' : 'genre',
    '%a' : 'artist',
    '%l' : 'album',
    '%t' : 'title',
    '%n' : 'tracknumber',
    '%y' : 'date',
    }
    
formatoptions = [ 'mp3', 'flac', 'ogg' ]

###
# Functiions
###

def parseArgs():
  ap = (argparse.ArgumentParser(
    description='Create directory structure based on audio tags.'))
  ap.add_argument('-v','--verbose',action='store_true',help='Print failures')
  ap.add_argument('-c','--clean',action='store_true',help='Clean destination \
                                  of broken links and empty dirs before creation')
  ap.add_argument('--dn',nargs='+',required=True,choices=tagdict, \
                          help='IN ORDER! Directory level tags')
  ap.add_argument('--fn',nargs='+',required=True,choices=tagdict, \
                          help='IN ORDER! Tags for filenames')
  ap.add_argument('-f','--formats',nargs='+',default=formatoptions, \
                  choices=formatoptions,help='Formats to search for')
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

#Not implemented
def getAlbumArt(source,newbase):
  """ Check for image formats in newbase, if not there try to 
  symlink over from source """
# Better to not call this on every file lookup....
# Therefore: should be implemented after directory creation
# Query all bottom level created directories. Get first symlink, 
# check where it points, take the base path of destination (i.e. containing
# directory), look for image file formats, if found, symlink


def cleanDestination(dst):
  """Check the created directory for broken links and remove at the git go.
  Remove any empty directories """
  removeBrokeLinks(dst)
  removeEmptyDirs(dst)

def removeBrokeLinks(path):
  for root, dirs, files in os.walk(path):
    for fn in files:
      abspath = os.path.join(root,fn)
      print abspath
      if os.path.exists(abspath) is False:
        print "Removing broken link:", abspath
        os.remove(abspath)

def removeEmptyDirs(path):
  """ Remove empty directories recusively
  From: http://dev.enekoalonso.com/2011/08/06/python-script-remove-empty-folders/"""
  if not os.path.isdir(path):
    return
  # remove empty subfolders
  files = os.listdir(path)
  if len(files):
    for f in files:
      fullpath = os.path.join(path, f)
      if os.path.isdir(fullpath):
        removeEmptyDirs(fullpath)
  # if folder empty, delete it
  files = os.listdir(path)
  if len(files) == 0:
    print "Removing empty folder:", path
    os.rmdir(path)

def makeDirStructure(dirs,nametags,ext,source,base):
  """ Make directory structure based on tag order
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
  
def enchilada(v,encoding,dirs,names,dst):
  #Dumb count of succesful mp3 symbolic links
  made = 0 
  fails = []
  for f in encoding[0]:
    try:
      dirtags = getTagList(f,encoding[1],encoding[2],dirs)
      nametags = getTagList(f,encoding[1],encoding[2],names)
      #if v is True:
       # print dirtags, nametags
      makeDirStructure(dirtags,nametags,encoding[2],f,dst)
      made += 1
    except AttributeError or UnboundLocalError:
      fails.append(f)
      pass
  print "Successful %s makes: %i" % (encoding[2],made)
  return fails

###
# Main
###

def main():
  
  #Getting the arguments
  args = parseArgs()
  verbose = args.verbose              #Is Verbose
  src = os.path.abspath(args.src)     #Source directory
  dst = os.path.abspath(args.dst)     #Destination
  dirs = getDict(args.dn,tagdict)     #Directory name tags
  names = getDict(args.fn,tagdict)    #Filename tags
  formats = args.formats

  #Check POSIX environment
  if os.name is not 'posix':
    print 'Symmusic requires a posix environment!'
    sys.exit()

  #Check that dst isn't inside src
  if os.path.commonprefix([src, dst]) is src:
    print 'Destination is inside source. This is not good. Failing!'
    sys.exit()

  #Clean stuff up if requested
  if args.clean is True:
    print "Cleaning"
    cleanDestination(dst)
    
  #This is ugly...but there aren't many formats, and it is easy.
  if 'mp3' in formats:
    mp3 = getMusic(src,".mp3"), EasyID3, '.mp3'
    mp3fails = enchilada(verbose,mp3,dirs,names,dst)

  if 'flac' in formats:
    flac = getMusic(src,".flac"), FLAC, '.flac'
    flacfails = enchilada(verbose,flac,dirs,names,dst)

  if 'ogg' in formats:
    ogg = getMusic(src,".ogg"), OggVorbis, '.ogg'
    oggfails = enchilada(verbose,ogg,dirs,names,dst)

  if verbose is True:
    print '\n' + "FAILURES:" + '\n'
    print mp3fails
    print flacfails
    print oggfails
  
if __name__ == '__main__':
    main()


