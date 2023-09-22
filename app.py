from flask import Flask, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
app = Flask(__name__)
client = MongoClient("mongodb://mongo:27017/")
db = client.UnipiLibrary
users_collection = db.Users
admin_collection = db.Admin
books_available_collection = db.BooksAvailable
reservations_collection = db.Reservations



def is_user_logged_in():
    return "username" in session



def is_user():
    if is_user_logged_in():
        user = users_collection.find_one({"username": session["username"]})
        return user is not None
    return False



# Συνάρτηση που ελέγχει αν ο χρήστης είναι διαχειριστής
def is_admin():
    if is_user_logged_in():
        admin = admin_collection.find_one({"username": session["username"]})
        return admin is not None
    return False




# Σύνδεση 
@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        username = request.json.get("username")
        password = request.json.get("password")
        
        user = users_collection.find_one({"username": username, "password": password})
        admin = admin_collection.find_one({"username": username, "password": password})
        
        if user or admin:
            session["username"] = username
            return jsonify({"message": "Επιτυχής σύνδεση!"})
        else:
            return jsonify({"message": "Αποτυχία σύνδεσης!"}), 401



# Εγγραφή χρήστη
@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        name = request.json.get("name")
        lastname = request.json.get("lastname")
        email = request.json.get("email")
        password = request.json.get("password")
        date_of_birth = request.json.get("date_of_birth")
        
        # Προσθήκη χρήστη στο κατάλληλο collection
        users_collection.insert_many({
            "username": email,
            "password": password,
            "name": name,
            "lastname": lastname,
            "email": email,
            "date_of_birth": date_of_birth
        })

        return jsonify({"message": "Επιτυχής εγγραφή!"})



#Διαγραφή Λογαριασμού χρήστη
@app.route("/delete_account", methods=["DELETE"])
def delete_account():
    if request.method == "DELETE":
        if is_user():
            username = session["username"]
            
            # Διαγραφή του χρήστη από το collection Users
            users_collection.delete_one({"username": username})
            
            # Επιστροφή μηνύματος επιτυχούς διαγραφής
            return jsonify({"message": "Ο λογαριασμός σας διαγράφηκε επιτυχώς!"})
            
    return jsonify({"message": "Δεν είστε συνδεδεμένος ως χρήστης!"}), 401



# Αναζήτηση βιβλίων από χρήστη
@app.route("/search_books", methods=["GET"])
def search_books():
    if request.method == "GET":
        if not is_user_logged_in():
            return jsonify({"message": "Πρέπει να είστε συνδεδεμένοι για να αναζητήσετε βιβλία."}), 401
  
        title = request.args.get("title")
        author = request.args.get("author")
        isbn = request.args.get("isbn")
        
        # Αναζήτηση βιβλίων στη συλλογή BooksAvailable
        query = {}
        if title:
            query["title"] = {"$regex": title, "$options": "i"}
        if author:
            query["author"] = {"$regex": author, "$options": "i"}
        if isbn:
            query["isbn"] = isbn

        books = list(books_available_collection.find(query))
        
        return jsonify({"message": "Αποτελέσματα αναζήτησης βιβλίων", "books": books})
    

    
# Κράτηση βιβλίου από χήστη
@app.route("/reserve_book", methods=["POST"])
def reserve_book():
    if request.method == "POST":
        if is_user():
            isbn = request.json.get("isbn")
            
            # Εύρεση βιβλίου στη συλλογή BooksAvailable
            book = books_available_collection.find_one({"isbn": isbn})
            
            if book:
                # Έλεγχος αν το βιβλίο υπάρχει ήδη στις κρατήσεις
                existing_reservation = reservations_collection.find_one({"isbn": isbn, "username": session["username"]})
                
                if existing_reservation:
                    return jsonify({"message": "Το βιβλίο έχει ήδη κρατηθεί από εσάς."}), 400
                
                # Προσθήκη κράτησης στη συλλογή Reservations
                reservations_collection.insert_one({
                    "isbn": book["isbn"],
                    "title": book["title"],
                    "author": book["author"],
                    "username": session["username"]
                })
                
                # Διαγραφή του βιβλίου από τη συλλογή BooksAvailable
                books_available_collection.delete_one({"isbn": isbn})
                
                return jsonify({"message": "Επιτυχής κράτηση βιβλίου!"})
            else:
                return jsonify({"message": "Το βιβλίο δεν είναι διαθέσιμο!"}), 400
    return jsonify({"message": "Δεν είστε συνδεδεμένος ως χρήστης!"}), 401




# Έλεγχος διαθεσιμότητας βιβλίου (χρήστης)
@app.route("/check_availability/<string:isbn>", methods=["GET"])
def check_book_availability(isbn):
    if request.method == "GET":
        if is_user():
            # Εύρεση βιβλίου στη συλλογή Reservations με βάση το ISBN
            existing_reservation = reservations_collection.find_one({"isbn": isbn})
            
            if existing_reservation:
                # Εάν υπάρχει κράτηση, επιστροφή μηνύματος ότι το βιβλίο δεν είναι διαθέσιμο
                return jsonify({"message": "Το βιβλίο δεν είναι διαθέσιμο για κράτηση."})
            else:
                # Εάν δεν υπάρχει κράτηση, εύρεση του βιβλίου στη συλλογή BooksAvailable
                book = books_available_collection.find_one({"isbn": isbn})
                
                if book:
                    # Επιστροφή των στοιχείων του βιβλίου από το collection BooksAvailable
                    return jsonify({
                        "message": "Το βιβλίο είναι διαθέσιμο για κράτηση.",
                        "borrowingDays": book["borrowingDays"],
                        "summary": book["summary"]
                    })
                else:
                    return jsonify({"message": "Το βιβλίο δεν βρέθηκε."}), 404
    return jsonify({"message": "Δεν είστε συνδεδεμένος ως χρήστης!"}), 401





# Εμφάνιση κρατήσεων χρήστη
@app.route("/user_reservations", methods=["GET"])
def user_reservations():
    if request.method == "GET":
        if is_user():
            username = session["username"]
            
            # Αναζήτηση κρατήσεων του χρήστη στη συλλογή Reservations
            reservations = list(reservations_collection.find({"username": username}))
            
            return jsonify({"message": "Οι κρατήσεις του χρήστη", "reservations": reservations})



# Προσθήκη νέου βιβλίου από διαχειριστή
@app.route("/add_book", methods=["POST"])
def add_book():
    if request.method == "POST":
        if is_admin():
            isbn = request.json.get("isbn")
            
            # Ελέγχος αν το ISBN είναι μοναδικό
            existing_book = books_available_collection.find_one({"isbn": isbn})
            if existing_book:
                return jsonify({"message": "Το βιβλίο με το ίδιο ISBN υπάρχει ήδη!"}), 400
            
            title = request.json.get("title")
            author = request.json.get("author")
            datePublished = request.json.get("datePublished")
            summary = request.json.get("summary")
            numberOfPages = request.json.get("numberOfPages")
            borrowingDays = request.json.get("borrowingDays")

            # Προσθήκη νέου βιβλίου στη συλλογή BooksAvailable
            books_available_collection.insert_one({
                "isbn": isbn,
                "title": title,
                "author": author,
                "datePublished": datePublished,
                "summary": summary,
                "numberOfPages": numberOfPages,
                "borrowingDays": borrowingDays
            })
            
            return jsonify({"message": "Επιτυχής προσθήκη νέου βιβλίου!"})




    
#Εύρεση βιβλίου από διαχειριστή
@app.route("/admin_search_books_advanced", methods=["GET"])
def admin_search_books_advanced():
    if request.method == "GET":
        if is_admin():
            title = request.args.get("title")
            author = request.args.get("author")
            publication_date = request.args.get("publication_date")
            isbn = request.args.get("isbn")
            
            # Αναζήτηση βιβλίων στη συλλογή BooksAvailable
            query = {}
            if title:
                query["title"] = {"$regex": title, "$options": "i"}
            if author:
                query["author"] = {"$regex": author, "$options": "i"}
            if publication_date:
                query["publication_date"] = publication_date
            if isbn:
                query["isbn"] = isbn

            books = list(books_available_collection.find(query))
            
            return jsonify({"message": "Αποτελέσματα αναζήτησης βιβλίων", "books": books})
            
    return jsonify({"message": "Δεν είστε συνδεδεμένος ως διαχειριστής!"}), 401




# Ανανέωση ημερών κράτησης ενός βιβλίου από διαχειριστή
@app.route("/admin_update_borrowing_days/<isbn>", methods=["PUT"])
def admin_update_borrowing_days(isbn):
    if request.method == "PUT":
        if is_admin():
            new_borrowing_days = request.json.get("borrowingDays")
            
            # Ενημέρωση του βιβλίου στη συλλογή BooksAvailable
            result = books_available_collection.update_one({"isbn": isbn}, {"$set": {"borrowingDays": new_borrowing_days}})
            
            if result.modified_count > 0:
                return jsonify({"message": "Επιτυχής ανανέωση ημερών κράτησης!"})
            else:
                return jsonify({"message": "Το βιβλίο με ISBN {} δεν βρέθηκε!".format(isbn)}), 404
    
    return jsonify({"message": "Δεν είστε συνδεδεμένος ως διαχειριστής!"}), 401



# Διαγραφή βιβλίου βάσει ISBN από διαχειριστή
@app.route("/admin_delete_book/<isbn>", methods=["DELETE"])
def admin_delete_book(isbn):
    if request.method == "DELETE":
        if is_admin():
            # Εύρεση του βιβλίου με βάση το ISBN
            book = books_available_collection.find_one({"isbn": isbn})
            
            if book:
                # Διαγραφή του βιβλίου από τη συλλογή BooksAvailable
                books_available_collection.delete_one({"isbn": isbn})
                return jsonify({"message": "Επιτυχής διαγραφή βιβλίου!"})
            else:
                return jsonify({"message": "Το βιβλίο με ISBN {} δεν βρέθηκε!".format(isbn)}), 404

    return jsonify({"message": "Δεν είστε συνδεδεμένος ως διαχειριστής!"}), 401



#Εύρεση στοιχείων βιβλίου από διαχειριστή
@app.route("/admin_view_book_details/<isbn>", methods=["GET"])
def admin_view_book_details(isbn):
    if is_admin():
        book = books_available_collection.find_one({"isbn": isbn})
        if book:
            book_details = {
                "title": book["title"],
                "author": book["author"],
                "datePublished": book["datePublished"],
                "summary": book["summary"],
                "numberOfPages": book["numberOfPages"],
                "borrowingDays": book["borrowingDays"]
            }
            return jsonify({"message": "Στοιχεία βιβλίου", "book_details": book_details})
        else:
            return jsonify({"message": "Δεν βρέθηκε βιβλίο με το δοσμένο ISBN."}), 404
    return jsonify({"message": "Δεν είστε συνδεδεμένος ως διαχειριστής!"}), 401



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)