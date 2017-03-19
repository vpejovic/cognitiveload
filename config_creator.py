import ConfigParser

config = ConfigParser.RawConfigParser()

config.add_section('ColorRectangle')
config.set('ColorRectangle', 'width', 300)
config.set('ColorRectangle', 'height', 300)
config.set('ColorRectangle', 'opacity_step', 0.01)
config.set('ColorRectangle', 'opacity_time', 0.1)

with open('config.cfg', 'wb') as configfile:
    config.write(configfile)