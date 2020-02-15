##############################################################################
# Copyright 2019 SoundHound, Incorporated.  All rights reserved.
##############################################################################
import base64
import hashlib
import hmac
import http.client
import json
import threading
import time
import uuid
import urllib.parse
import struct
import gzip


try:
  import pySHSpeex
except ImportError:
  pass

HOUND_SERVER = "api.houndify.com"
TEXT_ENDPOINT = "/v1/text"
VOICE_ENDPOINT = "/v1/audio"
VERSION = "1.2.5"


class _BaseHoundClient(object):

    def __init__(self, clientID, clientKey, userID, hostname, proxyHost, proxyPort, proxyHeaders):
      self.clientID = clientID
      self.clientKey = base64.urlsafe_b64decode(clientKey)
      self.userID = userID
      self.hostname = hostname
      self.proxyHost = proxyHost
      self.proxyPort = proxyPort
      self.proxyHeaders = proxyHeaders
      self.gzip = True
      
      self.HoundRequestInfo = {
        "ClientID": clientID,
        "UserID": userID,
        "SDK": "python3",
        "SDKVersion": VERSION
      }


    def setHoundRequestInfo(self, key, value):
      """
      There are various fields in the HoundRequestInfo object that can
      be set to help the server provide the best experience for the client.
      Refer to the Houndify documentation to see what fields are available
      and set them through this method before starting a request
      """
      self.HoundRequestInfo[key] = value


    def removeHoundRequestInfo(self, key):
      """
      Remove request info field through this method before starting a request
      """
      self.HoundRequestInfo.pop(key, None)


    def setLocation(self, latitude, longitude):
      """
      Many domains make use of the client location information to provide
      relevant results.  This method can be called to provide this information
      to the server before starting the request.

      latitude and longitude are floats (not string)
      """
      self.HoundRequestInfo["Latitude"] = latitude
      self.HoundRequestInfo["Longitude"] = longitude
      self.HoundRequestInfo["PositionTime"] = int(time.time())


    def setConversationState(self, conversation_state):
      self.HoundRequestInfo["ConversationState"] = conversation_state
      if "ConversationStateTime" in conversation_state:
        self.HoundRequestInfo["ConversationStateTime"] = conversation_state["ConversationStateTime"]


    def _generateHeaders(self, requestInfo):
      requestID = str(uuid.uuid4())
      if "RequestID" in requestInfo:
        requestID = requestInfo["RequestID"]

      timestamp = str(int(time.time()))
      if "TimeStamp" in requestInfo:
        timestamp = str(requestInfo["TimeStamp"])

      HoundRequestAuth = self.userID + ";" + requestID
      h = hmac.new(self.clientKey, (HoundRequestAuth + timestamp).encode("utf-8"), hashlib.sha256)
      signature = base64.urlsafe_b64encode(h.digest()).decode("utf-8")
      HoundClientAuth = self.clientID + ";" + timestamp + ";" + signature

      headers = { 
        "Hound-Request-Info": json.dumps(requestInfo),
        "Hound-Request-Authentication": HoundRequestAuth,
        "Hound-Client-Authentication": HoundClientAuth
      }

      if "InputLanguageEnglishName" in requestInfo:
          headers["Hound-Input-Language-English-Name"] = requestInfo["InputLanguageEnglishName"]
      if "InputLanguageIETFTag" in requestInfo:
          headers["Hound-Input-Language-IETF-Tag"] = requestInfo["InputLanguageIETFTag"]

      return headers



class TextHoundClient(_BaseHoundClient):
    """
    TextHoundClient is used for making text queries for Hound
    """
    def __init__(self, clientID, clientKey, userID, requestInfo = dict(), hostname = HOUND_SERVER, proxyHost = None, proxyPort = None, proxyHeaders = None):
      _BaseHoundClient.__init__(self, clientID, clientKey, userID, hostname, proxyHost, proxyPort, proxyHeaders)
      self.HoundRequestInfo.update(requestInfo)
    

    def query(self, query):
      """
      Make a text query to Hound.

      query is the string of the query
      """
      headers = self._generateHeaders(self.HoundRequestInfo)
      if self.gzip:
        headers["Hound-Response-Accept-Encoding"] = "gzip";

      if self.proxyHost:
        conn = http.client.HTTPSConnection(self.proxyHost, self.proxyPort)
        conn.set_tunnel(self.hostname, headers = self.proxyHeaders) 
      else:
        conn = http.client.HTTPSConnection(self.hostname)
      
      conn.request("GET", TEXT_ENDPOINT + "?query=" + urllib.parse.quote(query), headers = headers)
      resp = conn.getresponse()

      raw_response = resp.read()

      try:
        if self.gzip:
          raw_response = gzip.decompress(raw_response)
        raw_response = raw_response.decode("utf-8")
        return json.loads(raw_response)
      except:
        return { "Error": raw_response }



class HoundListener(object):
    """
    HoundListener is an abstract base class that defines the callbacks
    that can be received while streaming speech to the server
    """
    def onPartialTranscript(self, transcript):
      """
      onPartialTranscript is fired when the server has sent a partial transcript
      in live transcription mode.  "transcript" is a string with the partial transcript
      """
      pass
    def onFinalResponse(self, response):
      """
      onFinalResponse is fired when the server has completed processing the query
      and has a response.  "response" is the JSON object (as a Python dict) which
      the server sends back.
      """
      pass
    def onError(self, err):
      """
      onError is fired if there is an error interacting with the server.  It contains
      the parsed JSON from the server.
      """
      pass



class StreamingHoundClient(_BaseHoundClient):
    """
    StreamingHoundClient is used to send streaming audio to the Hound
    server and receive live transcriptions back
    """
    def __init__(self, clientID, clientKey, userID, requestInfo = dict(), hostname = HOUND_SERVER, sampleRate = 16000, enableVAD = True, useSpeex = False, proxyHost = None, proxyPort = None, proxyHeaders = None):
      """
      clientID and clientKey are "Client ID" and "Client Key" 
      from the Houndify.com web site.
      """
      _BaseHoundClient.__init__(self, clientID, clientKey, userID, hostname, proxyHost, proxyPort, proxyHeaders)
      
      self.sampleRate = sampleRate
      self.useSpeex = useSpeex
      self.enableVAD = enableVAD
      
      self.HoundRequestInfo["PartialTranscriptsDesired"] = True
      self.HoundRequestInfo.update(requestInfo)


    def setSampleRate(self, sampleRate):
      """
      Override the default sample rate of 16 khz for audio.

      NOTE that only 8 khz and 16 khz are supported
      """
      if sampleRate == 8000 or sampleRate == 16000:
        self.sampleRate = sampleRate
      else:
        raise Exception("Unsupported sample rate")


    def start(self, listener=HoundListener()):
      """
      This method is used to make the actual connection to the server and prepare
      for audio streaming.

      listener is a HoundListener (or derived class) object
      """
      self.audioFinished = False
      self.lastResult = None
      self.buffer = bytes()

      if self.proxyHost:
        self.conn = http.client.HTTPSConnection(self.proxyHost, self.proxyPort)
        self.conn.set_tunnel(self.hostname, headers = self.proxyHeaders) 
      else:
        self.conn = http.client.HTTPSConnection(self.hostname)

      self.conn.putrequest("POST", VOICE_ENDPOINT)

      headers = self._generateHeaders(self.HoundRequestInfo)
      headers["Transfer-Encoding"] = "chunked";
      if self.gzip:
        headers["Hound-Response-Accept-Encoding"] = "gzip";

      for header in headers:
        self.conn.putheader(header, headers[header])
      self.conn.endheaders()
      
      self.callbackTID = threading.Thread(target = self._callback, args = (listener,))
      self.callbackTID.start()

      audio_header = self._wavHeader(self.sampleRate)
      if self.useSpeex:
        audio_header = pySHSpeex.Init(self.sampleRate == 8000)
      self._send(audio_header)

      
    def fill(self, data):
      """
      After successfully connecting to the server with start(), pump PCM samples
      through this method.

      data is 16-bit, 8 KHz/16 KHz little-endian PCM samples.
      Returns True if the server detected the end of audio and is processing the data
      or False if the server is still accepting audio
      """
      # buffer gets flushed on next call to start()
      if self.audioFinished and self.enableVAD:
        return True

      self.buffer += data

      # 20ms 16-bit audio frame = (2 * 0.02 * sampleRate) bytes
      frame_size = int(2 * 0.02 * self.sampleRate)
      while len(self.buffer) >= frame_size:
        frame = self.buffer[:frame_size]
        self.buffer = self.buffer[frame_size:]
        if self.useSpeex:
          frame = pySHSpeex.EncodeFrame(frame)
        
        self._send(frame)   

      return False


    def finish(self):
      """
      Once fill returns True, call finish() to finalize the transaction.  finish will
      wait for all the data to be received from the server.

      After finish() is called, you can start another request with start() but each
      start() call should have a corresponding finish() to wait for the threads
      """

      if len(self.buffer) > 0:
        frame = self.buffer
        if self.useSpeex:
          padding_size = int(2 * 0.02 * self.sampleRate) - len(self.buffer)
          frame = frame + b'\x00' * padding_size
          frame = pySHSpeex.EncodeFrame(frame)
          
        self._send(frame)

      self._send("")
      self.callbackTID.join()
      return self.lastResult


    def _callback(self, listener):
      headers = ""
      body = ""
      is_chunked = False
      chunk_size = None
      content_length = None
      transcripts_done = False
      headers_done = False

      gen = self._readline(self.conn.sock)
      while True:
        try:
          line = gen.send(chunk_size)
        except:
          break

        if self.gzip and line[:3] == b"\x1f\x8b\x08":
          line = gzip.decompress(line)

        line = line.decode("utf-8")
        
        if not headers_done:
          headers += line + "\r\n"
          header = line.strip().lower()
          if header == "transfer-encoding: chunked":
            is_chunked = True
          if "content-length" in header:
            content_length = int(header.split(" ")[1])
          if headers.endswith("\r\n\r\n"):
            headers_done = True
            chunk_size = content_length
          continue

        body += line

        if is_chunked and chunk_size is None:
          chunk_size = int(line, 16)
          continue

        chunk_size = None

        try:
          parsedMsg = json.loads(line)
        except:
          break

        if "Status" in parsedMsg and parsedMsg["Status"] == "Error":
          self.lastResult = parsedMsg
          listener.onError(parsedMsg)  
          self.audioFinished = True
          return     

        if "Format" in parsedMsg:
          if parsedMsg["Format"] == "SoundHoundVoiceSearchParialTranscript" or parsedMsg["Format"] == "HoundVoiceQueryPartialTranscript":
            listener.onPartialTranscript(parsedMsg["PartialTranscript"])
            if "SafeToStopAudio" in parsedMsg and parsedMsg["SafeToStopAudio"]:
              self.audioFinished = True
            if "Done" in parsedMsg and parsedMsg["Done"]:
              transcripts_done = True

          if parsedMsg["Format"] == "SoundHoundVoiceSearchResult" or parsedMsg["Format"] == "HoundQueryResult":
            self.lastResult = parsedMsg
            listener.onFinalResponse(parsedMsg)
            return

      self.lastResult = { "Error": body }
      listener.onError({ "Error": body })
      self.audioFinished = True


    def _wavHeader(self, sampleRate=16000):
      genHeader = "RIFF".encode("UTF-8")
      genHeader += struct.pack("<L", 36) #ChunkSize - dummy   
      genHeader += "WAVE".encode("UTF-8")
      genHeader += "fmt ".encode("UTF-8")             
      genHeader += struct.pack("<L", 16) #Subchunk1Size
      genHeader += struct.pack("<H", 1)  #AudioFormat - PCM
      genHeader += struct.pack("<H", 1)  #NumChannels
      genHeader += struct.pack("<L", sampleRate) #SampleRate
      genHeader += struct.pack("<L", 8 * sampleRate) #ByteRate
      genHeader += struct.pack("<H", 2) #BlockAlign
      genHeader += struct.pack("<H", 16) #BitsPerSample
      genHeader += "data".encode("UTF-8")
      genHeader += struct.pack("<L", 0) #Subchunk2Size - dummy

      return genHeader


    def _send(self, msg):
      if self.conn:
        if (isinstance(msg, str)): 
          msg = msg.encode("utf-8")
        chunk_size = "%x\r\n" % len(msg)
        try:
          self.conn.send(chunk_size.encode("utf-8"))
          self.conn.send(msg + "\r\n".encode("utf-8"))
        except:
          self.conn.close()
          self.conn = None


    def _readline(self, socket):
      response_buffer = bytearray()
      chunk_size = None
      separator = "\r\n".encode("utf-8")
      msg_size = 4096

      while True:
        msg = socket.recv(msg_size)
        if not msg: break
        
        response_buffer += msg
 
        while True:
          if chunk_size is not None:
            if len(response_buffer) < (chunk_size+2): break
            chunk = response_buffer[:chunk_size]
            response_buffer = response_buffer[chunk_size+2:]

          else:
            split_buffer = response_buffer.split(separator, 1)
            if len(split_buffer) == 1: break
            chunk = split_buffer[0]
            response_buffer = split_buffer[1]

          chunk_size = yield chunk

      if response_buffer: yield response_buffer

      