# encoding: UTF-8

import os
import logging
import struct
import StringIO
from membership.models import Contact
from membership.utils import log_change
from django.utils.translation import ugettext_lazy as _

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

logger = logging.getLogger("membership.changed_addresses")

def Parser(filehandle):
    """Parser generator"""
    # TODO: support for person who has moved to abroad
    if type(filehandle) == type(""):
        filehandle = StringIO.StringIO(filehandle)
        print('stringio')
    personfields = (11, 3, 8, 1, 70, 30, 25, 4, 1,
                    8, 5, 30, 71, 30, 5, 30, 71, 30)
    companyfields = (11, 3, 8, 1, 50, 50, 25, 4, 1,
                    8, 5, 30, 71, 30, 5, 30, 71, 30)
    personlabels = ('customer_number', 'service_number', 'saving_date', 
                        'customer_type', 'name', 'old_last_name', 
                        'identification_number', 'status', 'transaction',
                        'address_date', 'new_postal_code', 'new_post_office', 
                        'new_street_address', 'new_address_family_id', 
                        'old_postal_code', 'old_post_office', 
                        'old_street_address', 'old_address_family_id')
    companylabels = ('customer_number', 'service_number', 'saving_date', 
                        'customer_type', 'name', 'operating_name', 
                        'identification_number', 'status', 'transaction',
                        'address_date', 'new_postal_code', 'new_post_office', 
                        'new_street_address', 'new_address_family_id', 
                        'old_postal_code', 'old_post_office', 
                        'old_street_address', 'old_address_family_id')
    fmtstring = ''.join('%ds' % f for f in personfields)
    personparse = struct.Struct(fmtstring).unpack_from
    fmtstring = ''.join('%ds' % f for f in companyfields)
    companyparse = struct.Struct(fmtstring).unpack_from
    for line in filehandle:
        if len(line) < 197:
            logger.error('Too short row found!')
            continue
        if line[22] == '1':
            # Person
            fields = personparse(line)
            yield fields_to_dict(personlabels, fields)
        elif line[22] == '2':
            # Company
            fields = companyparse(line)
            yield fields_to_dict(companylabels, fields)

def fields_to_dict(keys, values):
    retval = {}
    for key, value in zip(keys, values):
        retval[key] = " ".join(value.strip().split()
                              ).decode('ISO-8859-1').encode('utf-8')
    return retval

def update_contact(record, log_user=None):
    if 'operating_name' in record:
        # organization member
        contacts = Contact.objects.filter(
                                       organization_name__iexact=record['name'])
    else:
        last_name = record['name'].split()[0]
        first_name = record['name'].split()[1]
        contacts = Contact.objects.filter(last_name__iexact=last_name,
                            first_name__iexact=first_name)
    contacts = contacts.filter(postal_code__exact=record['old_postal_code'],
                            post_office__iexact=record['old_post_office'],
                            street_address__iexact=record['old_street_address'])
    contacts = contacts.all()
    if len(contacts) == 0:
        msg = 'Cannot find contact for record %s on address %s %s %s' % (
                    record['name'],record['old_street_address'],
                    record['old_postal_code'],record['old_post_office'])
        logging.error(msg)
        return (msg, None)
    for contact in contacts:
        before = contact.__dict__.copy()
        contact.street_address = record['new_street_address']
        contact.postal_code = record['new_postal_code']
        contact.post_office = record['new_post_office']
        print('save')
        contact.save()
        after = contact.__dict__.copy()
        if log_user == None:
            log_user = User.objects.get(id=1) # Get sikteeri user
        log_change(contact, log_user, before, after)
        logging.info('Updated contact %s' % contact)
    return (_('Contact %s updated' % contact), contact)

def changed_addresses(filehandle, user=None):
    messages = []
    for record in Parser(filehandle):
       msg = update_contact(record, user)
       if msg:
           messages.append(msg)
    return messages


class Command(BaseCommand):
    args = '<file1> [<file2>] ...'
    help = '''Import changed addresses from Itella's information service'''
    
    def handle(self, *args, **options):
        for cfile in args:
            logger.info("Starting the processing of file %s." %
                os.path.abspath(cfile))
            f = open(cfile, 'r')
            changed_addresses(f)