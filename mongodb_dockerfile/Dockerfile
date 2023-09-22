# Χρησιμοποιήστε την επίσημη εικόνα MongoDB
FROM mongo:latest

# Δημιουργία ενός φακέλου στον container για τα δεδομένα
VOLUME /data/db

# Ακούστε σε όλες τις διεπαφές
CMD ["mongod", "--bind_ip_all"]
