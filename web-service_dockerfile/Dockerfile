# Χρησιμοποιούμε την επίσημη εικόνα Python
FROM python:3.8

# Εγκατάσταση των απαιτούμενων βιβλιοθηκών
RUN pip install Flask Flask-PyMongo

# Προσθέτουμε τον κώδικα του Flask Web Service στο container
COPY app.py /app.py

# Ρυθμίζουμε τον περιβάλλοντα χρόνο για το Flask
ENV FLASK_APP=/app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Εκκινούμε την εφαρμογή Flask
CMD ["flask", "run"]
