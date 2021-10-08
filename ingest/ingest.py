import logging, mailbox, os
import quopri
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    ComplexField,
    CorsOptions,
    SearchIndex,
    ScoringProfile,
    SearchFieldDataType,
    SimpleField,
    SearchableField
)

load_dotenv()

import_file = os.getenv('IMPORT_FILE')
service_name = os.getenv('SERVICE_NAME')
admin_key = os.getenv('ADMIN_KEY')
index_name = os.getenv('INDEX_NAME')

def main():
    logger = setup_logging()
    logger.info('Starting import')
    logger.info('Importing from: {}'.format(import_file))
    logger.info('Importing to: {}'.format(service_name))
    try:
        mbox = mailbox.mbox(import_file)
    except Exception as e:
        logger.exception(e)

    if not is_mailbox(mbox):
        logger.error("No mailbox found")
        exit(1)

    for message in mbox:
        print_message(message)


def print_message(message):
    print("-"*80)
    print(message['subject'])
    print(message['from'])
    print(message['to'])
    print(message['date'])
    message_content = get_message_content(message)
    clean_text = strip_html_tags(message_content)
    print(clean_text)

def get_message_content(msg):
    try:
        if msg.is_multipart():
            useful_content=[]
            for part in msg.walk():
                content_type=part.get_content_type()
                if content_type=='text/plain'\
                or content_type=='text/html'\
                or content_type=='text/enriched'\
                or content_type=='multipart/mixed':
                    payload=part.get_payload(decode=True)
                    if payload==None:
                        payload=b''
                    useful_content.append(payload)
            content=b''.join(useful_content)
        else:
            content = msg.get_payload(decode=True)
        msg = quopri.decodestring(content)
        return msg
    except Exception as e:
        print(e)
        return 'Message not extractable.'

def strip_html_tags(content):
    soup = BeautifulSoup(content)
    return soup.get_text(' ', strip=True)

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    return logger

def is_mailbox(mbox):
    if len(mbox.keys()) > 0:
        return True
    else:
        return False

main()