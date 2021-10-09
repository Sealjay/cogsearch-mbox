"""Ingests a mailbox into Azure Cognitive Search."""
import calendar
import logging
import mailbox
import os
import quopri
import uuid
from email.utils import (
    parsedate_to_datetime,
)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    CorsOptions,
    SearchableField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
)
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

import_file = os.getenv("IMPORT_FILE")
service_name = os.getenv("SERVICE_NAME")
admin_key = os.getenv("ADMIN_KEY")
index_name = os.getenv("INDEX_NAME")

azure_logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
azure_logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def main() -> None:
    """The main application function."""
    logger.info("Starting import")
    logger.info("Importing from: %s", import_file)
    logger.info("Importing to: %s", service_name)
    try:
        mbox = mailbox.mbox(import_file)
        logger.info("Mailbox successfully opened")
    except Exception as error:
        logger.exception(error)

    if not is_mailbox(mbox):
        logger.error("No mailbox found")
        exit(1)
    else:
        logger.info("Mailbox contains emails")

    try:
        search_client, admin_client = get_search_clients()
        logger.info("Search client and admin client successfully created")
    except Exception as error:
        logger.exception(error)

    try:
        create_search_index(admin_client)
        logger.info("Search index successfully created")
    except Exception as error:
        logger.exception(error)
    documents = [document_from_message(message) for message in mbox]
    logger.info("Uploading %d documents", len(documents))
    try:
        upload_mbox_message(search_client, documents)
        logger.info("Documents successfully uploaded")
    except Exception as error:
        logger.exception(error)


def print_message(message: mailbox.Message):
    """Prints the message to the console.

    Args:
        message ([type]): [description]
    """
    print("-" * 80)
    print(document_from_message(message))


def document_from_message(message: mailbox.Message) -> dict:
    message_content = get_message_content(message)
    clean_text = strip_html_tags(message_content)
    import_uuid = str(uuid.uuid4())
    search_document = {
        "@search.action": "upload",
        "ImportId": import_uuid,
        "MessageSubject": message["subject"],
        "MessageFrom": message["from"],
        "MessageTo": message["to"],
        "MessageDate": convert_to_edm_datetime_offset(message["date"]),
        "MessageContent": clean_text,
    }
    return search_document


def convert_to_edm_datetime_offset(email_date_str):
    """Converts a UTC date to an EDM datetime offset.

    Args:
        utc_date: The UTC date to convert.

    Returns:
        str: The EDM datetime offset.
    """
    datetime_object = parsedate_to_datetime(email_date_str)
    utc_date_str = datetime_object.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return utc_date_str


def get_message_content(msg: mailbox.Message) -> bytes:
    """Returns the message content as bytes.

    Args:
        msg (mailbox.Message): The message to get the content from.

    Returns:
        bytes: The message content as bytes.
    """
    try:
        if msg.is_multipart():
            useful_content = []
            for part in msg.walk():
                content_type = part.get_content_type()
                if (
                    content_type == "text/plain"
                    or content_type == "text/html"
                    or content_type == "text/enriched"
                    or content_type == "multipart/mixed"
                ):
                    payload = part.get_payload(decode=True)
                    if payload == None:
                        payload = b""
                    useful_content.append(payload)
            content = b"".join(useful_content)
        else:
            content = msg.get_payload(decode=True)
        msg = quopri.decodestring(content)
        return msg
    except Exception as error:
        logger.error(error)
        return "Message not extractable."


def strip_html_tags(content: bytes) -> str:
    """Strips HTML tags from the content.

    Args:
        content (bytes): The content to strip.

    Returns:
        str: The stripped content.
    """
    soup = BeautifulSoup(content, features="html.parser")
    return soup.get_text(" ", strip=True)


def is_mailbox(mbox: mailbox.Mailbox) -> bool:
    """Checks if the mailbox is a valid mailbox.

    Args:
        mbox (mailbox.Mailbox): The mailbox to check.

    Returns:
        bool: True if the mailbox is a valid mailbox.
    """
    if len(mbox.keys()) > 0:
        return True
    else:
        return False


def get_search_clients():
    """Returns a SearchClient instance for Azure Cognitive Search.

    Returns:
        SearchClient: A SearchClient instance.
        AdminClient: A SearchIndex client instance.
    """
    endpoint = "https://{}.search.windows.net/".format(service_name)
    search_client = SearchClient(
        endpoint,
        index_name,
        AzureKeyCredential(admin_key),
    )
    admin_client = SearchIndexClient(
        endpoint,
        AzureKeyCredential(admin_key),
    )
    return search_client, admin_client


def upload_mbox_message(search_client: SearchClient, documents: dict):
    try:
        logger.info("Preparing to submit documents")
        result = search_client.upload_documents(documents)
        logger.info(f"Upload of new documents succeeded: {result[0].succeeded}")
        return result
    except Exception as error:
        logger.error(error)


def create_search_index(admin_client):
    fields = [
        SimpleField(name="ImportId", type=SearchFieldDataType.String, key=True),
        SearchableField(
            name="MessageSubject",
            type=SearchFieldDataType.String,
            facetable=True,
            filterable=True,
            sortable=True,
            analyzer_name="en.lucene",
        ),
        SearchableField(
            name="MessageFrom",
            type=SearchFieldDataType.String,
            facetable=True,
            filterable=True,
            sortable=True,
        ),
        SearchableField(
            name="MessageTo",
            type=SearchFieldDataType.String,
            facetable=True,
            filterable=True,
            sortable=True,
        ),
        SearchableField(
            name="MessageContent",
            type=SearchFieldDataType.String,
            analyzer_name="en.lucene",
        ),
        SimpleField(
            name="MessageDate",
            type=SearchFieldDataType.DateTimeOffset,
            facetable=True,
            filterable=True,
            sortable=True,
        ),
    ]
    cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
    scoring_profiles = []
    suggester = [{"name": "sg", "source_fields": ["MessageFrom", "MessageTo"]}]
    index = SearchIndex(
        name=index_name,
        fields=fields,
        scoring_profiles=scoring_profiles,
        suggesters=suggester,
        cors_options=cors_options,
    )
    try:
        result = admin_client.create_index(index)
        logger.info("Index created: %s", result.name)
    except Exception as ex:
        logger.error("Failed to create index: %s", ex)


main()
