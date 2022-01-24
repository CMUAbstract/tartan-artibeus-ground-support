# Usage: python3 rx_test.py /path/to/dev
# Parameters:
#  /path/to/dev: path to device, e.g. /dev/ttyUSB0
# Output:
#  Prints results to the command line

# import Python modules
import copy     # deepcopy
import datetime # datetime
import enum     # Enum
import math     # floor
import serial   # serial
import sys      # accessing script arguments
import time     # sleep

################################################################################

# Special values for testing the COMM board

HWID  = 0x0001
msgid = 0x0000
SRC   = 0x01
DST   = 0x01

# "constants"

## TAOLST General Constants
CMD_MAX_LEN  = 258
DATA_MAX_LEN = 249
START_BYTE_0 = 0x22
START_BYTE_1 = 0x69
DEST_COMM    = 0x01
DEST_CTRL    = 0x0a
DEST_EXPT    = 0x02
DEST_TERM    = 0x00

## TAOLST Command Op Codes
APP_GET_TELEM_OPCODE         = 0x17
APP_GET_TIME_OPCODE          = 0x13
APP_REBOOT_OPCODE            = 0x12
APP_SET_TIME_OPCODE          = 0x14
APP_TELEM_OPCODE             = 0x18
BOOTLOADER_ACK_OPCODE        = 0x01
BOOTLOADER_ERASE_OPCODE      = 0x0c
BOOTLOADER_JUMP_OPCODE       = 0x0b
BOOTLOADER_NACK_OPCODE       = 0x0f
BOOTLOADER_PING_OPCODE       = 0x00
BOOTLOADER_WRITE_PAGE_OPCODE = 0x02
COMMON_ACK_OPCODE            = 0x10
COMMON_ASCII_OPCODE          = 0x11
COMMON_NACK_OPCODE           = 0xff

## TAOLST Command Enum Parameters
BOOTLOADER_ACK_REASON_PONG   = 0x00
BOOTLOADER_ACK_REASON_ERASED = 0x01
BOOTLOADER_ACK_REASON_JUMP   = 0xff

## TAOLST Command Indices
START_BYTE_0_INDEX = 0
START_BYTE_1_INDEX = 1
MSG_LEN_INDEX      = 2
HWID_LSB_INDEX     = 3
HWID_MSB_INDEX     = 4
MSG_ID_LSB_INDEX   = 5
MSG_ID_MSB_INDEX   = 6
DEST_ID_INDEX      = 7
OPCODE_INDEX       = 8
DATA_START_INDEX   = 9

## Space time epoch
J2000 = datetime.datetime(\
 2000, 1, 1,11,58,55,816000,\
 tzinfo=datetime.timezone.utc\
)

# enums

class RxCmdBuffState(enum.Enum):
  START_BYTE_0 = 0x00
  START_BYTE_1 = 0x01
  MSG_LEN      = 0x02
  HWID_LSB     = 0x03
  HWID_MSB     = 0x04
  MSG_ID_LSB   = 0x05
  MSG_ID_MSB   = 0x06
  DEST_ID      = 0x07
  OPCODE       = 0x08
  DATA         = 0x09
  COMPLETE     = 0x0a

# helper functions

## Converts DEST_ID to string
def dest_id_to_str(dest_id):
  if dest_id==DEST_COMM:
    return 'comm'
  elif dest_id==DEST_CTRL:
    return 'ctrl'
  elif dest_id==DEST_EXPT:
    return 'expt'
  elif dest_id==DEST_TERM:
    return 'term'
  else:
    return '?'

## Converts BOOTLOADER_ACK_REASON to string
def bootloader_ack_reason_to_str(bootloader_ack_reason):
  if bootloader_ack_reason==BOOTLOADER_ACK_REASON_PONG:
    return 'pong'
  elif bootloader_ack_reason==BOOTLOADER_ACK_REASON_ERASED:
    return 'erased'
  elif bootloader_ack_reason==BOOTLOADER_ACK_REASON_JUMP:
    return 'jump'
  else:
    return '?'

## Converts a list of command bytes (ints) to a human-readable string
def cmd_bytes_to_str(data):
  s = ''
  extra = ''
  if data[OPCODE_INDEX] == APP_GET_TELEM_OPCODE:
    s += 'app_get_telem'
  elif data[OPCODE_INDEX] == APP_GET_TIME_OPCODE:
    s += 'app_get_time'
  elif data[OPCODE_INDEX] == APP_REBOOT_OPCODE:
    s += 'app_reboot'
    if data[MSG_LEN_INDEX] == 0x0a:
      extra = ' delay:'+str(\
       (data[DATA_START_INDEX+3]<<24) | \
       (data[DATA_START_INDEX+2]<<16) | \
       (data[DATA_START_INDEX+1]<< 8) | \
       (data[DATA_START_INDEX+0]<< 0)   \
      )
  elif data[OPCODE_INDEX] == APP_SET_TIME_OPCODE:
    s += 'app_set_time'
    extra = \
     ' sec:' + str(\
      data[DATA_START_INDEX+3]<<24 | \
      data[DATA_START_INDEX+2]<<16 | \
      data[DATA_START_INDEX+1]<< 8 | \
      data[DATA_START_INDEX+0]<< 0   \
     ) + \
     ' ns:'  + str(\
      data[DATA_START_INDEX+7]<<24 | \
      data[DATA_START_INDEX+6]<<16 | \
      data[DATA_START_INDEX+5]<< 8 | \
      data[DATA_START_INDEX+4]<< 0   \
     )
  elif data[OPCODE_INDEX] == APP_TELEM_OPCODE:
    s += 'app_telem'
    extra = ' hex_telem:'
    for i in range(0,data[MSG_LEN_INDEX]-0x06):
      extra += '{:02x}'.format(data[DATA_START_INDEX+i])
  elif data[OPCODE_INDEX] == BOOTLOADER_ACK_OPCODE:
    s += 'bootloader_ack'
    if data[MSG_LEN_INDEX] == 0x07:
      extra = ' reason:'+'0x{:02x}'.format(data[DATA_START_INDEX])+\
       '('+bootloader_ack_reason_to_str(data[DATA_START_INDEX])+')'
  elif data[OPCODE_INDEX] == BOOTLOADER_ERASE_OPCODE:
    s += 'bootloader_erase'
    if data[MSG_LEN_INDEX] == 0x07:
      extra = ' status:'+'0x{:02x}'.format(data[DATA_START_INDEX])
  elif data[OPCODE_INDEX] == BOOTLOADER_JUMP_OPCODE:
    s += 'bootloader_jump'
  elif data[OPCODE_INDEX] == BOOTLOADER_NACK_OPCODE:
    s += 'bootloader_nack'
  elif data[OPCODE_INDEX] == BOOTLOADER_PING_OPCODE:
    s += 'bootloader_ping'
  elif data[OPCODE_INDEX] == BOOTLOADER_WRITE_PAGE_OPCODE:
    s += 'bootloader_write_page'
    extra = ' subpage_id:'+str(data[DATA_START_INDEX])
    if data[MSG_LEN_INDEX] == 0x87:
      extra += ' hex_data:'
      for i in range(0,data[MSG_LEN_INDEX]-0x07):
        extra += '{:02x}'.format(data[DATA_START_INDEX+1+i])
  elif data[OPCODE_INDEX] == COMMON_ACK_OPCODE:
    s += 'common_ack'
  elif data[OPCODE_INDEX] == COMMON_ASCII_OPCODE:
    s += 'common_ascii'
    extra = ' "'
    for i in range(0,data[MSG_LEN_INDEX]-0x06):
      extra += chr(data[DATA_START_INDEX+i])
    extra += '"'
  elif data[OPCODE_INDEX] == COMMON_NACK_OPCODE:
    s += 'common_nack'
  s += ' hw_id:0x{:04x}'.format(\
   (data[HWID_MSB_INDEX]<<8)|(data[HWID_LSB_INDEX]<<0)\
  )
  s += ' msg_id:0x{:04x}'.format(\
   (data[MSG_ID_MSB_INDEX]<<8)|(data[MSG_ID_LSB_INDEX]<<0)\
  )
  s += ' src_id:0x{:01x}'.format((data[DEST_ID_INDEX]>>4)&0x0f)
  s += '('+dest_id_to_str((data[DEST_ID_INDEX]>>4)&0x0f)+')'
  s += ' dst_id:0x{:01x}'.format((data[DEST_ID_INDEX]>>0)&0x0f)
  s += '('+dest_id_to_str((data[DEST_ID_INDEX]>>0)&0x0f)+')'
  s += extra
  return s

# classes

## Command for transmitting
# TODO: a "valid" state variable that indicates whether data is a valid command
class TxCmd:
  def __init__(self, opcode, hw_id, msg_id, src, dst):
    self.data = [0x00]*CMD_MAX_LEN
    self.data[START_BYTE_0_INDEX] = START_BYTE_0
    self.data[START_BYTE_1_INDEX] = START_BYTE_1
    self.data[HWID_LSB_INDEX]     = (hw_id  >> 0) & 0xff
    self.data[HWID_MSB_INDEX]     = (hw_id  >> 8) & 0xff
    self.data[MSG_ID_LSB_INDEX]   = (msg_id >> 0) & 0xff
    self.data[MSG_ID_MSB_INDEX]   = (msg_id >> 8) & 0xff
    self.data[DEST_ID_INDEX]      = (src << 4) | (dst << 0)
    self.data[OPCODE_INDEX]       = opcode
    if self.data[OPCODE_INDEX] == APP_GET_TELEM_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == APP_GET_TIME_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == APP_REBOOT_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == APP_SET_TIME_OPCODE:
      self.data[MSG_LEN_INDEX]      = 0x0e
      self.data[DATA_START_INDEX+0] = 0x00
      self.data[DATA_START_INDEX+1] = 0x00
      self.data[DATA_START_INDEX+2] = 0x00
      self.data[DATA_START_INDEX+3] = 0x00
      self.data[DATA_START_INDEX+4] = 0x00
      self.data[DATA_START_INDEX+5] = 0x00
      self.data[DATA_START_INDEX+6] = 0x00
      self.data[DATA_START_INDEX+7] = 0x00
    elif self.data[OPCODE_INDEX] == APP_TELEM_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x54
      for i in range(0,0x54-0x06):
        self.data[DATA_START_INDEX+i] = 0x00
    elif self.data[OPCODE_INDEX] == BOOTLOADER_ACK_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == BOOTLOADER_ERASE_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == BOOTLOADER_JUMP_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == BOOTLOADER_NACK_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == BOOTLOADER_PING_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == BOOTLOADER_WRITE_PAGE_OPCODE:
      self.data[MSG_LEN_INDEX]    = 0x07
      self.data[DATA_START_INDEX] = 0x00
    elif self.data[OPCODE_INDEX] == COMMON_ACK_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == COMMON_ASCII_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == COMMON_NACK_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    else:
      self.data[MSG_LEN_INDEX] = 0x06

  def app_reboot(self, delay):
    if self.data[OPCODE_INDEX] == APP_REBOOT_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x0a
      b0 = (delay >>  0) & 0xff # LSB
      b1 = (delay >>  8) & 0xff
      b2 = (delay >> 16) & 0xff
      b3 = (delay >> 24) & 0xff # MSB
      self.data[DATA_START_INDEX+0] = b0
      self.data[DATA_START_INDEX+1] = b1
      self.data[DATA_START_INDEX+2] = b2
      self.data[DATA_START_INDEX+3] = b3

  def app_set_time(self, sec, ns):
    if self.data[OPCODE_INDEX] == APP_SET_TIME_OPCODE:
      s0 = (sec >>  0) & 0xff # LSB
      s1 = (sec >>  8) & 0xff
      s2 = (sec >> 16) & 0xff
      s3 = (sec >> 24) & 0xff # MSB
      n0 = ( ns >>  0) & 0xff # LSB
      n1 = ( ns >>  8) & 0xff
      n2 = ( ns >> 16) & 0xff
      n3 = ( ns >> 24) & 0xff # MSB
      self.data[DATA_START_INDEX+0] = s0
      self.data[DATA_START_INDEX+1] = s1
      self.data[DATA_START_INDEX+2] = s2
      self.data[DATA_START_INDEX+3] = s3
      self.data[DATA_START_INDEX+4] = n0
      self.data[DATA_START_INDEX+5] = n1
      self.data[DATA_START_INDEX+6] = n2
      self.data[DATA_START_INDEX+7] = n3

  def app_telem(self, telem):
    if self.data[OPCODE_INDEX] == APP_TELEM_OPCODE and len(telem)==78:
      for i in range(0,len(telem)):
        self.data[DATA_START_INDEX+i] = telem[i]

  def bootloader_ack(self, reason):
    if self.data[OPCODE_INDEX] == BOOTLOADER_ACK_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x07
      self.data[DATA_START_INDEX] = reason

  def bootloader_erase(self, status):
    if self.data[OPCODE_INDEX] == BOOTLOADER_ERASE_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x07
      self.data[DATA_START_INDEX] = status

  def bootloader_write_page(self, page_number, page_data=[]):
    if self.data[OPCODE_INDEX] == BOOTLOADER_WRITE_PAGE_OPCODE:
      self.data[DATA_START_INDEX] = page_number
      if len(page_data)==128:
        self.data[MSG_LEN_INDEX] = 0x87
        for i in range(0,len(page_data)):
          self.data[DATA_START_INDEX+1+i] = page_data[i]

  def common_ascii(self, ascii):
    if self.data[OPCODE_INDEX] == COMMON_ASCII_OPCODE:
      if len(ascii)<=249:
        self.data[MSG_LEN_INDEX] = 0x06+len(ascii)
        for i in range(0,len(ascii)):
          self.data[DATA_START_INDEX+i] = ord(ascii[i])

  def get_byte_count(self):
    return self.data[MSG_LEN_INDEX]+0x03

  def clear(self):
    self.data = [0x00]*CMD_MAX_LEN

  def __str__(self):
    return cmd_bytes_to_str(self.data)

## Buffer for received TAOLST commands
class RxCmdBuff:
  def __init__(self):
    self.state = RxCmdBuffState.START_BYTE_0
    self.start_index = 0
    self.end_index = 0
    self.data = [0x00]*CMD_MAX_LEN

  def clear(self):
    self.state = RxCmdBuffState.START_BYTE_0
    self.start_index = 0
    self.end_index = 0
    self.data = [0x00]*CMD_MAX_LEN

  def append_byte(self, b):
    if self.state == RxCmdBuffState.START_BYTE_0:
      if b==START_BYTE_0:
        self.data[START_BYTE_0_INDEX] = b
        self.state = RxCmdBuffState.START_BYTE_1
    elif self.state == RxCmdBuffState.START_BYTE_1:
      if b==START_BYTE_1:
        self.data[START_BYTE_1_INDEX] = b
        self.state = RxCmdBuffState.MSG_LEN
      else:
        self.clear()
    elif self.state == RxCmdBuffState.MSG_LEN:
      if 0x06 <= b and b <= 0xff:
        self.data[MSG_LEN_INDEX] = b
        self.start_index = 0x09
        self.end_index = b+0x03
        self.state = RxCmdBuffState.HWID_LSB
      else:
        self.clear()
    elif self.state == RxCmdBuffState.HWID_LSB:
      self.data[HWID_LSB_INDEX] = b
      self.state = RxCmdBuffState.HWID_MSB
    elif self.state == RxCmdBuffState.HWID_MSB:
      self.data[HWID_MSB_INDEX] = b
      self.state = RxCmdBuffState.MSG_ID_LSB
    elif self.state == RxCmdBuffState.MSG_ID_LSB:
      self.data[MSG_ID_LSB_INDEX] = b
      self.state = RxCmdBuffState.MSG_ID_MSB
    elif self.state == RxCmdBuffState.MSG_ID_MSB:
      self.data[MSG_ID_MSB_INDEX] = b
      self.state = RxCmdBuffState.DEST_ID
    elif self.state == RxCmdBuffState.DEST_ID:
      self.data[DEST_ID_INDEX] = b
      self.state = RxCmdBuffState.OPCODE
    elif self.state == RxCmdBuffState.OPCODE:
      self.data[OPCODE_INDEX] = b
      if self.start_index < self.end_index:
        self.state = RxCmdBuffState.DATA
      else:
        self.state = RxCmdBuffState.COMPLETE
    elif self.state == RxCmdBuffState.DATA:
      if self.start_index < self.end_index:
        self.data[self.start_index] = b
        self.start_index += 1
        if self.start_index == self.end_index:
          self.state = RxCmdBuffState.COMPLETE
      else:
        self.state = RxCmdBuffState.COMPLETE
    elif self.state == RxCmdBuffState.COMPLETE:
      pass

  def get_byte_count(self):
    return self.data[MSG_LEN_INDEX]+0x03

  def __str__(self):
    if self.state == RxCmdBuffState.COMPLETE:
      return cmd_bytes_to_str(self.data)
    else:
      pass

## Buffer for transmitted TAOLST commands
class TxCmdBuff:
  def __init__(self):
    self.empty = True
    self.start_index = 0
    self.end_index = 0
    self.data = [0x00]*CMD_MAX_LEN

  def clear(self):
    self.empty = True
    self.start_index = 0
    self.end_index = 0
    self.data = [0x00]*CMD_MAX_LEN

  def generate_reply(self, rx_cmd_buff):
    if rx_cmd_buff.state==RxCmdBuffState.COMPLETE and self.empty:
      self.data[START_BYTE_0_INDEX] = START_BYTE_0
      self.data[START_BYTE_1_INDEX] = START_BYTE_1
      self.data[HWID_LSB_INDEX] = rx_cmd_buff.data[HWID_LSB_INDEX]
      self.data[HWID_MSB_INDEX] = rx_cmd_buff.data[HWID_MSB_INDEX]
      self.data[MSG_ID_LSB_INDEX] = rx_cmd_buff.data[MSG_ID_LSB_INDEX]
      self.data[MSG_ID_MSB_INDEX] = rx_cmd_buff.data[MSG_ID_MSB_INDEX]
      self.data[DEST_ID_INDEX] = \
       (0x0f & rx_cmd_buff.data[DEST_ID_INDEX]) << 4 | \
       (0xf0 & rx_cmd_buff.data[DEST_ID_INDEX]) >> 4
      if rx_cmd_buff.data[OPCODE_INDEX] == APP_GET_TELEM_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x54
        self.data[OPCODE_INDEX] = APP_TELEM_OPCODE
        for i in range(0,self.data[MSG_LEN_INDEX]-0x06):
          self.data[DATA_START_INDEX+i] = 0x00
      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_GET_TIME_OPCODE:
        td  = datetime.datetime.now(tz=datetime.timezone.utc) - J2000
        sec = math.floor(td.total_seconds())
        ns  = td.microseconds * 1000
        sec_bytes = bytearray(sec.to_bytes(4,'little'))
        ns_bytes  = bytearray( ns.to_bytes(4,"little"))
        self.data[MSG_LEN_INDEX] = 0x0e
        self.data[OPCODE_INDEX] = APP_SET_TIME_OPCODE
        self.data[DATA_START_INDEX+0] = sec_bytes[0]
        self.data[DATA_START_INDEX+1] = sec_bytes[1]
        self.data[DATA_START_INDEX+2] = sec_bytes[2]
        self.data[DATA_START_INDEX+3] = sec_bytes[3]
        self.data[DATA_START_INDEX+4] =  ns_bytes[0]
        self.data[DATA_START_INDEX+5] =  ns_bytes[1]
        self.data[DATA_START_INDEX+6] =  ns_bytes[2]
        self.data[DATA_START_INDEX+7] =  ns_bytes[3]
      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_REBOOT_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_SET_TIME_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_TELEM_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_ACK_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_ERASE_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_NACK_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_PING_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_WRITE_PAGE_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_JUMP_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == COMMON_ACK_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_ACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == COMMON_ASCII_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == COMMON_NACK_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE

  def get_byte_count(self):
    return self.data[MSG_LEN_INDEX]+0x03

  def __str__(self):
    return cmd_bytes_to_str(self.data)

# initialize script arguments
dev = '' # serial device

# parse script arguments
if len(sys.argv)==2:
  dev = sys.argv[1]
else:
  print(\
   'Usage: '\
   'python3 rx_test.py '\
   '/path/to/dev'\
  )
  exit()

# Create serial object
try:
  serial_port = serial.Serial(port=dev,baudrate=115200)
except:
  print('Serial port object creation failed:')
  print('  '+dev)
  exit()

################################################################################

# Set up test support variables
rx_cmd_buff = RxCmdBuff()
tx_cmd_buff = TxCmdBuff()

# Listen and reply
cmd_count = 0
while cmd_count<12:
  while rx_cmd_buff.state != RxCmdBuffState.COMPLETE:
    if serial_port.in_waiting>0:
      bytes = serial_port.read(1)
      for b in bytes:
        rx_cmd_buff.append_byte(b)
  tx_cmd_buff.generate_reply(rx_cmd_buff)
  byte_i = 0
  while byte_i < tx_cmd_buff.get_byte_count():
    serial_port.write(tx_cmd_buff.data[byte_i].to_bytes(1, byteorder='big'))
    byte_i += 1
  print('rxcmd: '+str(rx_cmd_buff)+'\n')
  print('reply: '+str(tx_cmd_buff)+'\n')
  rx_cmd_buff.clear()
  tx_cmd_buff.clear()
  cmd_count += 1
