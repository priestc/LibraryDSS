from models import Library
from giotto.primitives import ALL_DATA

def start_publish(identity, size, hash):
    """
    Based on the size and hash, determine which storage engine should get this
    new upload.
    """
    library = Library.get(identity)
    return library.get_storage(size)

def finish_publish(identity, url, size, hash, metadata=ALL_DATA):
    library = Library.get(identity)
    library.add_item(url, size, hash, metadata)

def query(identity, query):
    library = Library.get(identity)
    return library.execute_query(query)