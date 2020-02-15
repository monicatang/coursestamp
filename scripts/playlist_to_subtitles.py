from __future__ import unicode_literals
import youtube_dl
import sys

"""
Downloads all subtitles from a playlist into the current directory.

youtube-dl --ignore-errors --yes-playlist --write-auto-sub --skip-download --output "Title=%(title)s_Id=%(id)s" 'https://www.youtube.com/playlist?list=PLLssT5z_DsK-h9vYZkQkYNWcItqhlRJLN'  
"""
def process_playlist(link):
  ydl_opts = {"ignoreerrors": True, "writeautomaticsub": True, "skip_download": True, "outtmpl" : "Title=%(title)s_Id=%(id)s"}
  with youtube_dl.YoutubeDL(ydl_opts) as ydl:
      ydl.download([link])

if __name__ == '__main__':
  args = sys.argv
  assert len(args) == 2, "Must provide playlist"
  process_playlist(args[1])