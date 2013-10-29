from ScrollsSocketClient import ScrollsSocketClient
from parser import PriceParser
import logging
import sqlsoup

class PriceBot(object):
    config = None
    trade_db = None
    scrolls = None
    scroll_list = None

    def __init__(self, config):
        self.config = config

        # init logging
        logging.basicConfig(filename=self.config.log_file, level=logging.INFO)

        # init the trade db
        connect_string = ('mysql://%(trade_db_user)s:%(trade_db_password)s@'
                            '%(trade_db_host)s:%(trade_db_port)i/%(trade_db_database)s') % config
        self.trade_db = sqlsoup.SQLSoup(connect_string)

        # init the scrolls client
        self.scrolls = ScrollsSocketClient(self.config.username, self.config.password)

        # subscribe to the FirstConnect event
        self.scrolls.subscribe('FirstConnect', self.connect)

        # login to the server
        self.scrolls.login()

    def connect(self, message):
        self.scrolls.send({'msg': 'JoinLobby'})

        for room_name in self.config.join_rooms:
            self.scrolls.send({'msg': 'RoomEnter', 'roomName': room_name})

        self.scrolls.subscribe('CardTypes', self.update_scroll_list)
        self.scrolls.send({'msg': 'CardTypes'})

    def room_chat(self, message):
        # log
        logging.info(message)

        # parse wtb/wts
        parsed = None
        parsed = self.parser.parse(message)

        if parsed:
            self.insert(parsed)

    def insert(self, params):
        """
        Perform the insert to the trade db
        """
        self.trade_db.execute('''
            INSERT INTO prices SET
                scroll_id = :scroll_id,
                time = UNIX_TIMESTAMP(),
                price = :price,
                user = :user,
                room = :room,
                type = :type ON DUPLICATE KEY UPDATE
                time = UNIX_TIMESTAMP(),
                price = :price,
                room = :room
                ''',
                params=params
        )

        self.trade_db.commit()

    def update_scroll_list(self, message):
        """
        Store a list of all the scrolls
        """

        # init parser, pass in scroll list
        self.parser = PriceParser(message['cardTypes'])

        # start listening for chat messages
        self.scrolls.subscribe('RoomChatMessage', self.room_chat)
