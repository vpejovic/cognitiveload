import ConfigParser

config = ConfigParser.RawConfigParser()
config.add_section('Main')
config.set('Main', 'task', 'color-rectangle')
config.set('Main', 'time_between_tasks', 7200)
config.set('Main', 'active_timeout', 120)
config.add_section('ColorRectangle')
config.set('ColorRectangle', 'width', 300)
config.set('ColorRectangle', 'height', 300)
config.set('ColorRectangle', 'opacity_step', 0.01)
config.set('ColorRectangle', 'opacity_time', 0.1)

with open('config.cfg', 'wb') as configfile:
    config.write(configfile)