# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: wire.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='wire.proto',
  package='',
  syntax='proto2',
  serialized_pb=_b('\n\nwire.proto\"7\n\x08\x45nvelope\x12\x1a\n\x04type\x18\x01 \x02(\x0e\x32\x0c.MessageType\x12\x0f\n\x07message\x18\x02 \x02(\x0c\"5\n\x13ProviderRegisterMsg\x12\x10\n\x08hostname\x18\x01 \x02(\t\x12\x0c\n\x04host\x18\x02 \x02(\t\"8\n\x14ProviderHeartbeatMsg\x12\x0c\n\x04host\x18\x01 \x02(\t\x12\x12\n\ndeviceList\x18\x02 \x02(\t\"2\n\x10\x44\x65vicePresentMsg\x12\x0e\n\x06serial\x18\x01 \x02(\t\x12\x0e\n\x06status\x18\x02 \x02(\t\"1\n\x0f\x44\x65viceStatusMsg\x12\x0e\n\x06serial\x18\x01 \x02(\t\x12\x0e\n\x06status\x18\x02 \x02(\t\"!\n\x0f\x44\x65viceAbsentMsg\x12\x0e\n\x06serial\x18\x01 \x02(\t*\x8a\x01\n\x0bMessageType\x12\x19\n\x15PROVIDER_REGISTER_MSG\x10\x01\x12\x16\n\x12\x44\x45VICE_PRESENT_MSG\x10\x02\x12\x15\n\x11\x44\x45VICE_ABSENT_MSG\x10\x03\x12\x15\n\x11\x44\x45VICE_STATUS_MSG\x10\x04\x12\x1a\n\x16PROVIDER_HEARTBEAT_MSG\x10\x05')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

_MESSAGETYPE = _descriptor.EnumDescriptor(
  name='MessageType',
  full_name='MessageType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='PROVIDER_REGISTER_MSG', index=0, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DEVICE_PRESENT_MSG', index=1, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DEVICE_ABSENT_MSG', index=2, number=3,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DEVICE_STATUS_MSG', index=3, number=4,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='PROVIDER_HEARTBEAT_MSG', index=4, number=5,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=323,
  serialized_end=461,
)
_sym_db.RegisterEnumDescriptor(_MESSAGETYPE)

MessageType = enum_type_wrapper.EnumTypeWrapper(_MESSAGETYPE)
PROVIDER_REGISTER_MSG = 1
DEVICE_PRESENT_MSG = 2
DEVICE_ABSENT_MSG = 3
DEVICE_STATUS_MSG = 4
PROVIDER_HEARTBEAT_MSG = 5



_ENVELOPE = _descriptor.Descriptor(
  name='Envelope',
  full_name='Envelope',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='Envelope.type', index=0,
      number=1, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=1,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='message', full_name='Envelope.message', index=1,
      number=2, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=14,
  serialized_end=69,
)


_PROVIDERREGISTERMSG = _descriptor.Descriptor(
  name='ProviderRegisterMsg',
  full_name='ProviderRegisterMsg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='hostname', full_name='ProviderRegisterMsg.hostname', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='host', full_name='ProviderRegisterMsg.host', index=1,
      number=2, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=71,
  serialized_end=124,
)


_PROVIDERHEARTBEATMSG = _descriptor.Descriptor(
  name='ProviderHeartbeatMsg',
  full_name='ProviderHeartbeatMsg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='host', full_name='ProviderHeartbeatMsg.host', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='deviceList', full_name='ProviderHeartbeatMsg.deviceList', index=1,
      number=2, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=126,
  serialized_end=182,
)


_DEVICEPRESENTMSG = _descriptor.Descriptor(
  name='DevicePresentMsg',
  full_name='DevicePresentMsg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='serial', full_name='DevicePresentMsg.serial', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='status', full_name='DevicePresentMsg.status', index=1,
      number=2, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=184,
  serialized_end=234,
)


_DEVICESTATUSMSG = _descriptor.Descriptor(
  name='DeviceStatusMsg',
  full_name='DeviceStatusMsg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='serial', full_name='DeviceStatusMsg.serial', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='status', full_name='DeviceStatusMsg.status', index=1,
      number=2, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=236,
  serialized_end=285,
)


_DEVICEABSENTMSG = _descriptor.Descriptor(
  name='DeviceAbsentMsg',
  full_name='DeviceAbsentMsg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='serial', full_name='DeviceAbsentMsg.serial', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=287,
  serialized_end=320,
)

_ENVELOPE.fields_by_name['type'].enum_type = _MESSAGETYPE
DESCRIPTOR.message_types_by_name['Envelope'] = _ENVELOPE
DESCRIPTOR.message_types_by_name['ProviderRegisterMsg'] = _PROVIDERREGISTERMSG
DESCRIPTOR.message_types_by_name['ProviderHeartbeatMsg'] = _PROVIDERHEARTBEATMSG
DESCRIPTOR.message_types_by_name['DevicePresentMsg'] = _DEVICEPRESENTMSG
DESCRIPTOR.message_types_by_name['DeviceStatusMsg'] = _DEVICESTATUSMSG
DESCRIPTOR.message_types_by_name['DeviceAbsentMsg'] = _DEVICEABSENTMSG
DESCRIPTOR.enum_types_by_name['MessageType'] = _MESSAGETYPE

Envelope = _reflection.GeneratedProtocolMessageType('Envelope', (_message.Message,), dict(
  DESCRIPTOR = _ENVELOPE,
  __module__ = 'wire_pb2'
  # @@protoc_insertion_point(class_scope:Envelope)
  ))
_sym_db.RegisterMessage(Envelope)

ProviderRegisterMsg = _reflection.GeneratedProtocolMessageType('ProviderRegisterMsg', (_message.Message,), dict(
  DESCRIPTOR = _PROVIDERREGISTERMSG,
  __module__ = 'wire_pb2'
  # @@protoc_insertion_point(class_scope:ProviderRegisterMsg)
  ))
_sym_db.RegisterMessage(ProviderRegisterMsg)

ProviderHeartbeatMsg = _reflection.GeneratedProtocolMessageType('ProviderHeartbeatMsg', (_message.Message,), dict(
  DESCRIPTOR = _PROVIDERHEARTBEATMSG,
  __module__ = 'wire_pb2'
  # @@protoc_insertion_point(class_scope:ProviderHeartbeatMsg)
  ))
_sym_db.RegisterMessage(ProviderHeartbeatMsg)

DevicePresentMsg = _reflection.GeneratedProtocolMessageType('DevicePresentMsg', (_message.Message,), dict(
  DESCRIPTOR = _DEVICEPRESENTMSG,
  __module__ = 'wire_pb2'
  # @@protoc_insertion_point(class_scope:DevicePresentMsg)
  ))
_sym_db.RegisterMessage(DevicePresentMsg)

DeviceStatusMsg = _reflection.GeneratedProtocolMessageType('DeviceStatusMsg', (_message.Message,), dict(
  DESCRIPTOR = _DEVICESTATUSMSG,
  __module__ = 'wire_pb2'
  # @@protoc_insertion_point(class_scope:DeviceStatusMsg)
  ))
_sym_db.RegisterMessage(DeviceStatusMsg)

DeviceAbsentMsg = _reflection.GeneratedProtocolMessageType('DeviceAbsentMsg', (_message.Message,), dict(
  DESCRIPTOR = _DEVICEABSENTMSG,
  __module__ = 'wire_pb2'
  # @@protoc_insertion_point(class_scope:DeviceAbsentMsg)
  ))
_sym_db.RegisterMessage(DeviceAbsentMsg)


# @@protoc_insertion_point(module_scope)
