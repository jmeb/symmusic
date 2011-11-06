#! /usr/bin/env python
#
# "THE BEER-WARE LICENSE" (Revision 42):
# jmeb wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. 
#
#

###
# Imports
###

import sys
import os
import re
import argparse
import time
import shutil
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
    
formatlist = [ 'mp3', 'flac', 'ogg' ]

###
# Functions
###

def parseArgs():
  ap = (argparse.ArgumentParser(
    description='Create directory structure based on audio tags.'))
  ap.add_argument('-v','--verbose',action='store_true',help='Print failures')
  ap.add_argument('-a','--art',action='store_true',help='Copy album art')
  ap.add_argument('-c','--clean',action='store_true',help='Clean destination \
                              of broken links and empty dirs before creation')
  ap.add_argument('-n','--number',type=int,help='Minimum number of songs in a \
                  directory. Use to ward against compilation nightmares.')
  ap.add_argument('--hours',type=int,help='Only use files modified in past N hours')
  ap.add_argument('--dn',nargs='+',required=True,choices=tagdict, \
                          help='IN ORDER! Directory level tags')
  ap.add_argument('--fn',nargs='+',required=True,choices=tagdict, \
                          help='IN ORDER! Tags for filenames')
  ap.add_argument('-f','--formats',nargs='+',default=formatlist, \
                  choices=formatlist,help='Formats to search for')
  ap.add_argument('-s', '--src', default=os.getcwd(),help='Source directory.')
  ap.add_argument('-d','--dst', required=True,help='Destination path') 
  return ap.parse_args()

def getDict(args,dictionary):
  """ Convert formats to extension labels. Return a list """
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
  """ Get an mp3 tag, fail without fanfare """
  try:
    tags = fun(f)
  except (ValueError,  mutagen.flac.FLACNoHeaderError):
    tags = 'Unknown'
  if tags.has_key(tagname):
    try:
      tag = tags[tagname][0]
      if tag:
        cleaned = tag.encode('UTF-8') 
        slashproofed = re.sub(r"/","-",cleaned) #Hack....
        return slashproofed
      else:
        return 'Unknown'
    except IndexError:
      pass
  else:
      return 'Unknown'
  
def getTagList(f,fun,ext,tagnames):
  """ Get multiple tags for a file, based on a given list """
  tags = []
  for tagname in tagnames:
    tag = getTag(f,fun,tagname)
    if tagname is 'album':
      tag = tag + ' [' + ext + ']'
    tags.append(tag)
  return tags

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
  except (OSError,  AttributeError):
    pass
  
def theWholeEnchilada(encoding,dirs,names,dst):
  """ A wrapper to bring everything together. Returns file paths that
  failed to create a symbolic link. """
  made = 0 
  fails = []
  for f in encoding[0]:
    try:
      dirtags = getTagList(f,encoding[1],encoding[2],dirs)
      nametags = getTagList(f,encoding[1],encoding[2],names)
      makeDirStructure(dirtags,nametags,encoding[2],f,dst)
      made += 1
    except AttributeError or UnboundLocalError:
      fails.append(f)
      pass
  print "Successful %s makes: %i" % (encoding[2],made)
  return fails

###
# Optional functions
###

def copyAlbumArt(pattern,dst):
  """ Check for image formats in newbase, if not there try to 
  symlink over from source """
  print "Copying Album Art...."
  symlinks = 0
  for root, dirs, files, in os.walk(dst):
    for fn in files:
      abspath = os.path.join(root,fn)
      dirpath = os.path.dirname(abspath)
      origin = os.readlink(abspath)
      origindir = os.path.dirname(origin)
      for oroot, odirs, ofiles, in os.walk(origindir):
        for f in ofiles:
          if f.endswith(pattern):
            if os.path.exists(os.path.join(dirpath,f)) is False:
              os.symlink(os.path.join(oroot,f),os.path.join(dirpath,f))
              symlinks += 1
  return symlinks

def cleanDestination(v,dst):
  """Check the created directory for broken links and remove them.
  Remove any empty directories """
  print "Cleaning..."
  brokelinks = removeBrokeLinks(v,dst)
  removeEmptyDirs(v,dst)
  return brokelinks

def removeBrokeLinks(v,path):
  """ Remove any broken symbolic links"""
  brokelinks = 0
  for root, dirs, files in os.walk(path):
    for fn in files:
      abspath = os.path.join(root,fn)
      if os.path.exists(abspath) is False:
        os.remove(abspath)
        brokelinks += 1
        if v is True:
          print "Removing broken link:", abspath
  return brokelinks

def removeEmptyDirs(v,path):
  """ Remove empty directories recusively. Taken from:
  http://dev.enekoalonso.com/2011/08/06/python-script-remove-empty-folders/"""
  if not os.path.isdir(path):
    return
  files = os.listdir(path)
  if len(files):
    for f in files:
      fullpath = os.path.join(path, f)
      if os.path.isdir(fullpath):
        removeEmptyDirs(v,fullpath)
  files = os.listdir(path)
  if len(files) == 0:
    os.rmdir(path)
    if v is True:
      print "Removing empty folder:", path

def removeSmallDirs(n,v,path):
  """ Remove small directories. Useful to avoid lots of compilation issues"""
  if not os.path.isdir(path):
      return
  files = os.listdir(path)
  if len(files):
    for f in files:
      fullpath = os.path.join(path, f)
      if os.path.isdir(fullpath):
        removeSmallDirs(n,v,fullpath)
  symcount = 0
  for f in files:
    fullpath = os.path.join(path, f)
    if os.path.islink(fullpath) is True:
      symcount +=1 
  if 0 < symcount < n :
    shutil.rmtree(path)
    if v is True:
      print "Removing small directory:", path

def getRecentFiles(files,hours):
  recentfiles = []
  modseconds = time.time() - ( hours * 3600 )
  for f in files:
    if os.path.getmtime(f) > modseconds:
      recentfiles.append(f)
  print "Files modified in the past %i hours: " % (hours), len(recentfiles) 
  return recentfiles    

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
  formats = args.formats              #Formats 
  verbose = args.verbose              #Verbose
  art = args.art                      #Artwork
  clean = args.clean                  #Clean destination
  number = args.number                #Minimum number for small dirs
  hours = args.hours

  #Check POSIX environment
  if os.name is not 'posix':
    print 'Symmusic requires a posix environment!'
    sys.exit()

  #Check that dst isn't inside src
  if os.path.commonprefix([src, dst]) is src:
    print 'Destination is inside source. This is not good. Failing!'
    sys.exit()

  #This is ugly...but there aren't many formats, and it is easy.
  if 'mp3' in formats:
    mp3 = [ getMusic(src,".mp3"), EasyID3, '.mp3' ]
    if hours:
      mp3[0] = getRecentFiles(mp3[0],hours)
    mp3fails = theWholeEnchilada(mp3,dirs,names,dst)

  if 'flac' in formats:
    flac = [ getMusic(src,".flac"), FLAC, '.flac' ]
    if hours:
      flac[0] = getRecentFiles(flac[0],hours)
    flacfails = theWholeEnchilada(flac,dirs,names,dst)

  if 'ogg' in formats:
    ogg = [ getMusic(src,".ogg"), OggVorbis, '.ogg' ]
    if hours:
      ogg[0] = getRecentFiles(ogg[0],hours)
    oggfails = theWholeEnchilada(ogg,dirs,names,dst)

  #Print failed lists for redirection
  if verbose is True:
    print '\n' + "FAILURES:" + '\n'
    print mp3fails, flacfails, oggfails

  #Clean out small directories
  if number:
    removeSmallDirs(args.number,verbose,dst)
    clean = True
  
  #Clean destination of empty dirs and broken links.
  if clean is True:
    brokelinks = cleanDestination(verbose,dst)
    print "Broken links removed: ", brokelinks

  #Copy album art if requested
  if art is True:
    artmakes = copyAlbumArt('.jpg',dst)
    print "Artwork images copied:", artmakes

if __name__ == '__main__':
    main()


