"""The server's own infrastructure: implementations of its domains' repository ports, such as its
database. Never shared and never chosen per deployment; that is what plugins/ is for. Only
api/main.py constructs these."""
