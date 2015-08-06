# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Conversions to translate between legacy YAML and OnePlatform protos."""

import re

from yaml_conversion.lib.google.appengine.api import appinfo


_SECONDS_PER_MINUTE = 60
_MILLISECONDS_PER_SECOND = 1000
_NANOSECONDS_PER_SECOND = 1000000000L

_COMMON_HANDLER_FIELDS = (
    'urlRegex',
    'login',
    'authFailAction',
    'securityLevel',
    'redirectHttpResponseCode',
)

_SCRIPT_FIELDS = (
    'scriptPath',
)

_HANDLER_FIELDS = {
    'staticFiles': (
        'path',
        'uploadPathRegex',
        'httpHeaders',
        'expiration',
        'applicationReadable',
        'mimeType',
        'requireMatchingFile',
    ),
    'script': _SCRIPT_FIELDS,
    'apiEndpoint': _SCRIPT_FIELDS,
}


def EnumConverter(prefix):
  """Create conversion function which translates from string to enum value.

  Args:
    prefix: Prefix for enum value. Expected to be an upper-cased value.

  Returns:
    A conversion function which translates from string to enum value.

  Raises:
    ValueError: If an invalid prefix (empty, non-upper-cased, etc.) prefix was
    provided.
  """
  if not prefix:
    raise ValueError('A prefix must be provided')
  if prefix != prefix.upper():
    raise ValueError('Upper-cased prefix must be provided')
  if prefix.endswith('_'):
    raise ValueError(
        'Prefix should not contain a trailing underscore: "%s"' % prefix)

  return lambda (value): '_'.join([prefix, value.upper()])


def Not(value):
  """Convert the given boolean value to the opposite value."""
  if not isinstance(value, bool):
    raise ValueError('Expected a boolean value. Got "%s"' % value)
  return not value


def ToJsonString(value):
  """Coerces a primitive value into a JSON-compatible string.

  Special handling for boolean values, since the Python version (True/False) is
  incompatible with the JSON version (true/false).

  Args:
    value: value to convert.

  Returns:
    Value as a string.

  Raises:
    ValueError: when a non-primitive value is provided.
  """
  if isinstance(value, (list, dict)):
    raise ValueError('Expected a primitive value. Got "%s"' % value)
  if isinstance(value, bool):
    return str(value).lower()
  return str(value)


def StringToInt(handle_automatic=False):
  """Create conversion function which converts from a string to an integer.

  Args:
    handle_automatic: Boolean indicating whether a value of "automatic" should
      be converted to 0.

  Returns:
    A conversion function which converts a string to an integer.
  """
  def Convert(value):
    if value == 'automatic' and handle_automatic:
      return 0
    return int(value)

  return Convert


def SecondsToDuration(value):
  """Convert seconds expressed as integer to a Duration value."""
  return '%ss' % int(value)


def LatencyToDuration(value):
  """Convert valid pending latency argument to a Duration value of seconds.

  Args:
    value: A string in the form X.Xs or XXms.

  Returns:
    Duration value of the given argument.

  Raises:
    ValueError: if the given value isn't parseable.
  """
  if not re.compile(appinfo._PENDING_LATENCY_REGEX).match(value):  # pylint: disable=protected-access
    raise ValueError('Unrecognized latency: %s' % value)
  if value == 'automatic':
    return None
  if value.endswith('ms'):
    return '%ss' % (float(value[:-2]) / _MILLISECONDS_PER_SECOND)
  else:
    return value


def IdleTimeoutToDuration(value):
  """Convert valid idle timeout argument to a Duration value of seconds.

  Args:
    value: A string in the form Xm or Xs

  Returns:
    Duration value of the given argument.

  Raises:
    ValueError: if the given value isn't parseable.
  """
  if not re.compile(appinfo._IDLE_TIMEOUT_REGEX).match(value):  # pylint: disable=protected-access
    raise ValueError('Unrecognized idle timeout: %s' % value)
  if value.endswith('m'):
    return '%ss' % (int(value[:-1]) * _SECONDS_PER_MINUTE)
  else:
    return value


def ExpirationToDuration(value):
  """Convert valid expiration argument to a Duration value of seconds.

  Args:
    value: String that matches _DELTA_REGEX.

  Returns:
    Time delta expressed as a Duration.

  Raises:
    ValueError: if the given value isn't parseable.
  """
  if not re.compile(appinfo._EXPIRATION_REGEX).match(value):  # pylint: disable=protected-access
    raise ValueError('Unrecognized expiration: %s' % value)
  delta = appinfo.ParseExpiration(value)
  return '%ss' % delta


def ConvertUrlHandler(handler):
  """Rejiggers the structure of the url handler based on its type.

  An extra level of message nesting occurs here, based on the handler type.
  Fields common to all handler types occur at the top-level, while
  handler-specific fields will go into a submessage based on handler type.

  For example, a static files handler is transformed as follows:
  Input {
    "urlRegex": "foo/bar.html",
    "path": "static_files/foo/bar.html"
  }
  Output {
    "urlRegex": "foo/bar.html",
    "staticFiles": {
      "path": "static_files/foo/bar.html"
    }
  }

  Args:
    handler: Result of converting handler according to schema.

  Returns:
    Handler which has moved fields specific to the handler's type to a
    submessage.
  """

  def AppendRegexToPath(path, regex):
    """Equivalent to os.path.join(), except uses forward slashes always."""
    return path.rstrip('/') + '/' + regex

  handler_type = _GetHandlerType(handler)

  # static_dir is syntactic sugar for static_files, so we "demote" any
  # static_dir directives we see to a static_files directive before
  # continuing.
  if handler_type == 'staticDirectory':
    tmp = {
        'path': AppendRegexToPath(handler['staticDir'], r'\1'),
        'uploadPathRegex': AppendRegexToPath(handler['staticDir'], '.*'),
        'urlRegex': AppendRegexToPath(handler['urlRegex'], '(.*)'),
    }
    del handler['staticDir']
    handler.update(tmp)
    handler_type = 'staticFiles'

  new_handler = {}
  new_handler[handler_type] = {}

  for field in _HANDLER_FIELDS[handler_type]:
    if field in handler:
      new_handler[handler_type][field] = handler[field]

  # Copy the common fields
  for common_field in _COMMON_HANDLER_FIELDS:
    if common_field in handler:
      new_handler[common_field] = handler[common_field]

  return new_handler


def _GetHandlerType(handler):
  """Get handler type of mapping.

  Args:
    handler: Original handler.

  Returns:
    Handler type determined by which handler id attribute is set.

  Raises:
    ValueError: when none of the handler id attributes are set.
  """
  if 'apiEndpoint' in handler:
    return 'apiEndpoint'
  elif 'staticDir' in handler:
    return 'staticDirectory'
  elif 'path' in handler:
    return 'staticFiles'
  elif 'scriptPath' in handler:
    return 'script'

  raise ValueError('Unrecognized handler type: %s' % handler)
