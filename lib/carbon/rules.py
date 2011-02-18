import re
from carbon.conf import OrderedConfigParser


rules = []
defaultRule = None
DEFAULT_CARBON_PORT = 2004


class Rule:
  def __init__(self, condition, destinations):
    self.condition = condition
    self.destinations = destinations

  def matches(self, metric):
    return bool( self.condition(metric) )


def loadRules(path):
  global defaultRule

  assert not rules, "rules already loaded"
  parser = OrderedConfigParser()

  if not parser.read(path):
    raise ValueError("Could not read rules file %s" % path)

  for section in parser.sections():
    if not parser.has_option(section, 'servers'):
      raise ValueError("Rules file %s section %s does not define a 'servers' list" % (path, section))

    servers = []
    for s in parser.get(section, 'servers').split(','):
      s = s.strip()

      if ':' in s:
        servers.append(s)
      else:
        servers.append('%s:%d' % (s, DEFAULT_CARBON_PORT))


    if parser.has_option(section, 'pattern'):
      assert not parser.has_option(section, 'default'), "Section %s contains both 'pattern' and 'default'. You must use one or the other." % section
      pattern = parser.get(section, 'pattern')
      regex = re.compile(pattern, re.I)
      rules.append( Rule(condition=regex.search, destinations=servers) )
      continue

    if parser.has_option(section, 'default'):
      if not parser.getboolean(section, 'default'): continue # just ignore default = false
      assert not defaultRule, "Two default rules? Seriously?"
      defaultRule = Rule(condition=lambda metric: True, destinations=servers)

  assert defaultRule, "No default rule defined. You must specify exactly one rule with 'default = true' instead of a pattern."


def getDestinations(metric):
  for rule in rules:
    if rule.matches(metric):
      return rule.destinations

  return defaultRule.destinations


def allDestinationServers():
  return set([server for server in rule.destinations for rule in rules])
