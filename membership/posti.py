# Functions to import Posti's changed addresses CSV:s
# http://www.posti.fi/yritysasiakkaat/laheta/asiakastietopalvelut/tiedotuspalvelu.html


def split_string(line, split_points, prefix=""):
    """
    Split string from points described in split_points tuple tuple.
    :param line: line to split
    :param split_points: split points and names for them
    :param prefix: prefix for keys
    :return: dict containing split values.
    """
    out = {}
    prev = 0
    for name, pos in split_points:
        out["%s%s" % (prefix, name)] = line[prev:pos].strip()
        prev = pos
    return out


post_format = (
    ("posti_customer_number", 11),
    ("service_code", 14),
    ("save_date", 22),
    ("customer_type", 23),
    ("full_name", 123),
    ("unique_identifier", 148),
    ("customer_status", 152),  # 0 dead or disbanded company, 1 adult or company office, 2 under age person, 9 not known
    ("event_code", 153),  # 0,1,2,3 language codes, 4,5 new address not known
    ("come_into_effect_date", 161),
    ("new_address", 297),
    ("old_address", 433),
    ("new_address_abroad", 633),
    ("new_address_country_code", 636),
    ("new_address_country_name", 666),
)

address_format = (
    ("post_number", 5),
    ("post_office", 35),
    ("address_street", 85),
    ("address_number_1", 90),
    ("address_alphabet_1", 91),
    ("address_separator", 92),
    ("address_number_2", 97),
    ("address_alphabet_2", 98),
    ("address_stair", 101),
    ("address_apartment_number", 105),
    ("address_room_alphabet", 106),
    ("address_family", 136),  # delivery point numeric identifier
)


class PostiChangedAddressParser(object):

    @staticmethod
    def parse_data(filehandle):
        """
        Parse fixed width formatted data received from Posti.
        :param filehandle: file like object
        :return: list of parsed data.
        """
        out = []
        for line in filehandle.readlines():
            line = line.decode("iso-8859-1")
            address_data = split_string(line, post_format)
            new_address = split_string(address_data['new_address'],
                                       address_format, prefix="new_")
            old_address = split_string(address_data['old_address'],
                                       address_format, prefix="old_")
            address_data.update(new_address)
            address_data.update(old_address)
            del(address_data['new_address'])
            del(address_data['old_address'])
            if address_data['customer_type'] == "1":
                n = address_data['full_name']
                address_data['full_name'] = n[:70]
                address_data['old_name'] = n[70:]
            else:
                n = address_data['full_name']
                address_data['full_name'] = n[:50]
                address_data['old_name'] = n[50:]
            out.append(address_data)
        return out


if __name__ == '__main__':
    f = open("/tmp/postidata.csv", 'rb')
    p = PostiChangedAddressParser()
    for address_data in p.parse_data(f):
        print("")
        for k, v in sorted(address_data.items(), key=lambda x: x[0]):
            print('%s: "%s"' % (k, v))