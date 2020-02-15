from __future__ import unicode_literals
import youtube_dl
import sys

"""
Downloads all subtitles from a playlist into the current directory.

youtube-dl --ignore-errors --yes-playlist --write-auto-sub --skip-download <playlist_link>  
"""
def process_playlist(link):
  ydl_opts = {"ignoreerrors": True, "writeautomaticsub": True, "skip_download": True}
  with youtube_dl.YoutubeDL(ydl_opts) as ydl:
      ydl.download([link])

if __name__ == '__main__':
  args = sys.argv
  assert len(args) == 2, "Must provide playlist"
  process_playlist(args[1])