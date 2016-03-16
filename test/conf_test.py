# Copyright 2015 Google Inc. All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

sys.argv.extend([
    '--config-value=flag_key=flag_value',
    '--config-value', 'other_flag=other_value',
])

import os.path
import unittest

import gflags

from openhtf import conf

conf.Declare('flag_key')
conf.Declare('other_flag')
conf.Declare('json_test_key')
conf.Declare('yaml_test_key')
conf.Declare('overridden_key')
conf.Declare('none_default', default_value=None)
conf.Declare('string_default', default_value='default')
conf.Declare('no_default')


class TestConf(unittest.TestCase):

  JSON_FILENAME = os.path.join(os.path.dirname(__file__), 'test_config.json')
  YAML_FILENAME = os.path.join(os.path.dirname(__file__), 'test_config.yaml')
  BAD_FILENAME = os.path.join(os.path.dirname(__file__), 'bad_config.txt')

  def tearDown(self):
    gflags.FLAGS.Reset()
    conf.Reset()

  def testJsonConfig(self):
    setattr(gflags.FLAGS, 'config-file', self.JSON_FILENAME)
    conf.Reset()
    self.assertEquals('json_test_value', conf.json_test_key)

  def testYamlConfig(self):
    setattr(gflags.FLAGS, 'config-file', self.YAML_FILENAME)
    conf.Reset()
    self.assertEquals('yaml_test_value', conf.yaml_test_key)

  def testLoadOverride(self):
    conf.Load(overridden_key='overridden_value')
    conf.Load(overridden_key='new_value')
    self.assertEquals('new_value', conf.overridden_key)

  def testLoadNoOverride(self):
    conf.Load(overridden_key='overridden_value')
    conf.Load(overridden_key='new_value', _override=False)
    self.assertEquals('overridden_value', conf.overridden_key)

  def testLoadFromDict(self):
    conf.LoadFromDict({'overridden_key': 'new_value'})
    self.assertEquals('new_value', conf.overridden_key)

  def testDefaults(self):
    self.assertEquals('default', conf.string_default)
    self.assertIsNone(conf.none_default)
    with self.assertRaises(conf.UnsetKeyError):
      conf.no_default

  def testFlagValues(self):
    self.assertEquals('flag_value', conf.flag_key)
    self.assertEquals('other_value', conf.other_flag)
    # Make sure flag value takes precedence, even if a value is loaded.
    conf.Load(flag_key='loaded_value')
    self.assertEquals('flag_value', conf.flag_key)

  def testAsDict(self):
    conf.Load(station_id='station_id')
    self.assertEquals({
      'station_id': 'station_id',
      'string_default': 'default',
      'none_default': None,
    }, conf._asdict())

  def testUndeclared(self):
    with self.assertRaises(conf.UndeclaredKeyError):
      conf.undeclared

  def testWeirdAttribute(self):
    with self.assertRaises(AttributeError):
      conf._dont_do_this
    with self.assertRaises(AttributeError):
      conf._dont_do_this_either = None

  def testCantSetViaAttribute(self):
    with self.assertRaises(AttributeError):
      conf.overridden_key = None

  def testMultipleDeclaration(self):
    conf.Declare('multiple')
    with self.assertRaises(conf.KeyAlreadyDeclaredError):
      conf.Declare('multiple')

  def testInvalidKey(self):
    with self.assertRaises(conf.InvalidKeyError):
      conf.Declare('_invalid')
    with self.assertRaises(conf.InvalidKeyError):
      conf.Declare('Invalid')

  def testBadConfigFile(self):
    setattr(gflags.FLAGS, 'config-file', self.BAD_FILENAME)
    with self.assertRaises(conf.ConfigurationInvalidError):
      conf.Reset()

  def testInjectPositionalArgs(self):
    @conf.InjectPositionalArgs
    def TestFunction(string_default, no_default, not_declared):
      self.assertEquals('default', string_default)
      self.assertEquals('passed_value', no_default)
      self.assertEquals('not_declared', not_declared)

    TestFunction(no_default='passed_value', not_declared='not_declared')

  def testInjectPositionalArgsOverrides(self):
    @conf.InjectPositionalArgs
    def TestFunction(string_default, no_default='new_default'):
      # Make sure when we pass a kwarg, it overrides the config value.
      self.assertEquals('overridden', string_default)
      # Make sure kwargs don't come from config, only positional args.
      self.assertEquals('new_default', no_default)

    TestFunction(string_default='overridden')

  def testInjectPositionalArgsClass(self):
    class TestClass(object):
      @conf.InjectPositionalArgs
      def __init__(self, string_default):
        self.string_default = string_default

    instance = TestClass()
    self.assertEquals('default', instance.string_default)
