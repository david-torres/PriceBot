from fuzzywuzzy import process
import re

class PriceParser(object):

    # list of proper scroll names
    scroll_names = []

    # dict of {'SCROLL_NAME': SCROLL_ID}
    scroll_ids = {}

    # regexes
    scroll_price_regex = '(.*?)\s+(\(?[0-9]+\)?\s?\.?,?[0-9]+?k?\s?g?)'
    scroll_noprice_regex = '([x|X]?[0-9]+[x|X]?\s+)?(.*)'
    wts_regex = 'wts/wtt|wts[\s|\-|:]'
    wtb_regex = 'wtb/wtt|wtb[\s|\-|:]'
    ex_alnum_regex = '[^a-zA-Z0-9\s\-,\.]'
    ex_num_regex = '[^0-9\.\,k]'
    each_regex = '\s+?ea(ch)?\s+?'
    multiples_regex = 'x?[0-9]+x?'
    common_delimiters = [',', '//', '||', '-', '|', '/']

    def __init__(self, scroll_list):
        """
        Initialized with the current set of scrolls for name matching
        """

        for scroll in scroll_list:
            self.scroll_names.append(scroll['name'])
            self.scroll_ids[scroll['name']] = scroll['id']

    def parse(self, message):
        parsed = None
        if message['text'].upper().find('WTS') > -1:
            parsed = self.parse_wts(message)
        elif message['text'].upper().find('WTB') > -1:
            parsed = self.parse_wtb(message)

        return parsed

    def parse_wts(self, message):
        """
        Parses a WTS message
        """

        wts_messages = []
        wts_pattern = re.compile(self.wts_regex, re.IGNORECASE)
        wts_matches = wts_pattern.search(message['text'])

        # we only want WTS messages
        if wts_matches and not message['text'].upper().find('WTB') > -1:
            sanitized_wts = self._sanitize_wts(message['text'])
            wts_messages_split = self._split_common_delimiters(sanitized_wts)
            for wts_message in wts_messages_split:
                price_matches = self._find_prices(wts_message.strip())

                if price_matches:
                    for match in price_matches:
                        scroll_name = self._sanitize_scroll_name(match[0])
                        scroll_price = self._sanitize_gold_amount(match[1])

                        if scroll_name and scroll_price:
                            wts = {
                                'scroll_id': self.scroll_ids[scroll_name],
                                'price': scroll_price,
                                'type': 1,
                                'user': message['from'],
                                'room': message['roomName']
                            }
                            wts_messages.append(wts)
                else:
                    noprice_matches = self._find_noprices(wts_message.strip())
                    for match in noprice_matches:
                        if match[1]:
                            scroll_name = self._sanitize_scroll_name(match[1])
                            if scroll_name:
                                wts = {
                                    'scroll_id': self.scroll_ids[scroll_name],
                                    'price': -1,
                                    'type': 1,
                                    'user': message['from'],
                                    'room': message['roomName']
                                }
                                wts_messages.append(wts)
        # done parsing WTS
        return wts_messages

    def parse_wtb(self, message):
        """
        Parses a WTB message
        """

        wtb_messages = []
        wtb_pattern = re.compile(self.wtb_regex, re.IGNORECASE)
        wtb_matches = wtb_pattern.search(message['text'])

        # we only want WTB messages
        if wtb_matches and not message['text'].upper().find('WTS') > -1:
            sanitized_wtb = self._sanitize_wtb(message['text'])
            wtb_messages_split = self._split_common_delimiters(sanitized_wtb)
            for wtb_message in wtb_messages_split:
                price_matches = self._find_prices(wtb_message.strip())

                if price_matches:
                    for match in price_matches:
                        scroll_name = self._sanitize_scroll_name(match[0])
                        scroll_price = self._sanitize_gold_amount(match[1])

                        if scroll_name and scroll_price:
                            wtb = {
                                'scroll_id': self.scroll_ids[scroll_name],
                                'price': scroll_price,
                                'type': 2,
                                'user': message['from'],
                                'room': message['roomName']
                            }
                            wtb_messages.append(wtb)
                else:
                    noprice_matches = self._find_noprices(wtb_message.strip())
                    for match in noprice_matches:
                        if match[1]:
                            scroll_name = self._sanitize_scroll_name(match[1])
                            if scroll_name:
                                wtb = {
                                    'scroll_id': self.scroll_ids[scroll_name],
                                    'price': -1,
                                    'type': 2,
                                    'user': message['from'],
                                    'room': message['roomName']
                                }
                                wtb_messages.append(wtb)
        # done parsing WTB
        return wtb_messages

    def _sanitize_wts(self, message):
        """
        Strip the WTS/WTT portion of the message, its irrelevant
        """
        wts_pattern = re.compile(self.wts_regex, re.IGNORECASE)
        message = wts_pattern.sub('', message)
        return message.strip()

    def _sanitize_wtb(self, message):
        """
        Strip the WTB/WTT portion of the message, its irrelevant
        """
        wtb_pattern = re.compile(self.wtb_regex, re.IGNORECASE)
        message = wtb_pattern.sub('', message)
        return message.strip()

    def _split_common_delimiters(self, message):
        """
        Split on common delimiters for better pattern matching
        """
        for delimiter in self.common_delimiters:
            if message.find(delimiter) > -1:
                return message.split(delimiter)

        return [message]

    def _find_prices(self, message):
        """
        Multiple match for Scroll_Name XXXg
        """
        # strip non alphanumeric chars
        ex_alnum = re.compile(self.ex_alnum_regex)
        message = ex_alnum.sub('', message.strip())

        pattern = re.compile(self.scroll_price_regex)
        return pattern.findall(message.strip())

    def _find_noprices(self, message):
        """
        Multiple match for Scroll_Name
        """
        # strip non alphanumeric chars
        ex_alnum = re.compile(self.ex_alnum_regex)
        message = ex_alnum.sub('', message.strip())

        pattern = re.compile(self.scroll_noprice_regex)
        return pattern.findall(message.strip())

    def _sanitize_scroll_name(self, scroll_name):
        """
        Sanitize and perform a fuzzy match on the scroll name
        """
        # rm each, ie. "Kinfolk Brave 100g ea"
        each_pattern = re.compile(self.each_regex, re.IGNORECASE)
        scroll_name = each_pattern.sub('', scroll_name)

        # rm multiples, ie. "Kinfolk Brave 100g x2"
        multiples_pattern = re.compile(self.multiples_regex, re.IGNORECASE)
        scroll_name = multiples_pattern.sub('', scroll_name)

        # need a confidence greater than 80 to consider it a match
        fuzzy_match = process.extractOne(scroll_name.strip(), self.scroll_names)
        if fuzzy_match and fuzzy_match[1] > 80:
            scroll_name = fuzzy_match[0]
            return scroll_name
        return None

    def _sanitize_gold_amount(self, scroll_price):
        """
        Sanitize the gold amount
        """
        # rm non numeric chars
        ex_num = re.compile(self.ex_num_regex, re.IGNORECASE)
        scroll_price = ex_num.sub('', scroll_price.strip())

        # check for 1.5k/1,5k style and sanitize
        if scroll_price.find('.') > -1 or scroll_price.find(',') > -1:
            scroll_price = scroll_price.replace('.', '').replace(',', '').strip()

            if scroll_price.lower().find('k') > -1:
                scroll_price = scroll_price.lower().replace('k', '00')
            else:
                scroll_price = scroll_price + '00'

        # try to cast as an int, if we succeed we have a clean price
        try:
            scroll_price = int(scroll_price)
            return scroll_price
        except ValueError:
            return None
