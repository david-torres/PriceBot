from pricebot import PriceBot
import yaml

config_file = open('config.yaml', 'r')
config = yaml.load(config_file)

pricebot = PriceBot(config)
