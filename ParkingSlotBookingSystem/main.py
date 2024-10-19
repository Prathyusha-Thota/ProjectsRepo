import datetime
import re

from flask import Flask, render_template, request, redirect, session
import pymongo
from bson import ObjectId
app = Flask(__name__)
app.secret_key = 'parking_booking_slot'
from Mail import send_email
my_client = pymongo.MongoClient("mongodb://localhost:27017")
my_database = my_client['parking_slot_booking']
admin_collection = my_database['admin']
parking_location_collection = my_database['parking_location']
parking_slot_collection = my_database['parking_slot']
customer_collection = my_database['customer']
reservation_collection = my_database['reservation']
payment_details_collection = my_database['payment_details']
review_collection = my_database['review']

query = {}
count = admin_collection.count_documents(query)
if count == 0:
    query = {'username': 'admin', 'password': 'admin'}
    admin_collection.insert_one(query)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin_login_action", methods=['post'])
def admin_login_action():
    username = request.form.get("username")
    password = request.form.get("password")
    query = {"username": username, "password": password}
    count = admin_collection.count_documents(query)
    if count > 0:
        admin = admin_collection.find_one(query)
        session['admin_id'] = str(admin['_id'])
        session['role'] = "admin"
        return redirect("/admin_home")
    else:
        return render_template("message.html", message="invalid login Details")


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")


@app.route("/customer_login")
def customer_login():
    return render_template("customer_login.html")


@app.route("/customer_login_action", methods=['post'])
def customer_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = customer_collection.count_documents(query)
    if count > 0:
        customer = customer_collection.find_one(query)
        session['customer_id'] = str(customer['_id'])
        session['role'] = "customer"
        return redirect("/customer_home")
    else:
        return render_template("message.html", message="invalid login Details")


@app.route("/customer_home")
def customer_home():
    return render_template("customer_home.html")


@app.route("/customer_registration")
def customer_registration():
    return render_template("customer_registration.html")


@app.route("/customer_registration_action", methods=['post'])
def customer_registration_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    city_name = request.form.get("city_name")
    state = request.form.get("state")
    zipcode = request.form.get("zipcode")
    DOB = request.form.get("DOB")
    address = request.form.get("address")
    #about = request.form.get("about")
    query = {"email": email}
    count = customer_collection.count_documents(query)
    if count > 0:
        return render_template("message.html", message="duplicate email address")

    query = {"phone": phone}
    count = customer_collection.count_documents(query)
    if count > 0:
        return render_template("message.html", message="duplicate phone number")

    query = {"first_name": first_name, "last_name":last_name, "city_name":city_name, "state":state, "zipcode":zipcode, "DOB":DOB, "email": email, "phone": phone, "password": password, "address": address, "confirm_password": confirm_password}
    customer_collection.insert_one(query)
    return render_template("message.html", message="CUSTOMER REGISTRATION SUCCESSFULLY")


@app.route("/locations")
def locations():
    query = {}
    parking_locations = parking_location_collection.find(query)
    parking_locations = list(parking_locations)
    return render_template("locations.html", parking_locations=parking_locations)


@app.route("/add_location_action")
def add_location_action():
    location_name = request.args.get("location_name")
    address = request.args.get("address")
    query = {"location_name": location_name}
    count = customer_collection.count_documents(query)
    if count > 0:
        return render_template("admin_message.html", message="duplicate location number")
    query = {"location_name": location_name, "address": address}
    parking_location_collection.insert_one(query)
    return render_template("admin_message.html", message="location Added successfully")


@app.route("/parking_slots")
def parking_slots():
    parking_locations = parking_location_collection.find()
    parking_locations = list(parking_locations)
    print(parking_locations)
    parking_slots = parking_slot_collection.find()
    return render_template("parking_slots.html", parking_locations=parking_locations, parking_slots=parking_slots, get_location_by_location_id=get_location_by_location_id)


def get_location_by_location_id(parking_location_id):
    location = parking_location_collection.find_one({'_id': ObjectId(parking_location_id)})
    return location


@app.route("/search_parking")
def search_parking():
    location_id = request.args.get("location_id")
    search_parking_area = request.args.get("search_parking_area")
    msg = request.args.get("msg")
    if search_parking_area is None:
        search_parking_area = ''
    if location_id is None:
        location_id = ''
    rgx1 = re.compile(".*" + search_parking_area + ".*", re.IGNORECASE)
    if search_parking_area != '' and location_id != '':
        query = {"parking_area_name": rgx1, "parking_location_id": ObjectId(location_id), "status": 'Available'}
    elif search_parking_area == '' and location_id != '':
        query = {"parking_location_id": ObjectId(location_id), "status": 'Available'}
    elif search_parking_area != '' and location_id == '':
        query = {"parking_area_name": rgx1, "status": 'Available'}
    elif search_parking_area == '' and location_id == '':
        query = {"status": 'Available'}
    parking_slots = parking_slot_collection.find(query)
    parking_slots = list(parking_slots)
    locations = parking_location_collection.find()
    return render_template("search_parking.html", parking_slots=parking_slots, search_parking_area=search_parking_area, msg=msg, locations=locations, get_location_by_location_id=get_location_by_location_id, get_ratings_by_id=get_ratings_by_id)


@app.route("/view_slots")
def view_slots():
    from_date_time = request.args.get('from_date_time')
    to_date_time = request.args.get('to_date_time')
    if from_date_time == None:
        from_date_time = datetime.datetime.now()
        to_date_time = from_date_time + datetime.timedelta(minutes=60)
        from_date_time = from_date_time.strftime("%Y-%m-%dT%H:%M")
        to_date_time = to_date_time.strftime("%Y-%m-%dT%H:%M")
    parking_slot_id = request.args.get("parking_slot_id")
    parking_slot = parking_slot_collection.find_one({"_id": ObjectId(parking_slot_id)})
    parking_location_id = parking_slot['parking_location_id']
    location = parking_location_collection.find_one({"_id": ObjectId(parking_location_id)})
    return render_template("view_slots.html", parking_slot=parking_slot, parking_slot_id=parking_slot_id, location=location, is_slot_reserved=is_slot_reserved, int=int, from_date_time=from_date_time, to_date_time=to_date_time, get_booked_slots_count=get_booked_slots_count)


@app.route("/book_slots")
def book_slots():
    parking_slot_id = request.args.get("parking_slot_id")
    from_date_time = request.args.get("from_date_time")
    to_date_time = request.args.get("to_date_time")
    number_of_slots = request.args.get("number_of_slots")
    from_date_time2 = datetime.datetime.strptime(from_date_time, "%Y-%m-%dT%H:%M")
    to_date_time2 = datetime.datetime.strptime(to_date_time, "%Y-%m-%dT%H:%M")
    parking_slot = parking_slot_collection.find_one({"_id": ObjectId(parking_slot_id)})
    price_per_hour = parking_slot['price_per_hour']
    diff = to_date_time2 - from_date_time2
    days = diff.days
    seconds = diff.seconds
    hours = seconds/3600
    if seconds % 3600 > 0:
        hours = hours + 1
    hours = hours + days * 24
    hours = int(hours)
    total_price = int(parking_slot['price_per_hour'])*hours
    return render_template("book_slots.html", parking_slot_id=parking_slot_id,from_date_time=from_date_time, to_date_time=to_date_time, hours=hours, total_price=total_price, parking_slot=parking_slot, price_per_hour=price_per_hour)


@app.route("/book_slots1", methods = ['post'])
def book_slots1():
    parking_slot_id = request.form.get("parking_slot_id")
    from_date_time = request.form.get("from_date_time")
    to_date_time = request.form.get("to_date_time")
    from_date_time = datetime.datetime.strptime(from_date_time, "%Y-%m-%dT%H:%M")
    to_date_time = datetime.datetime.strptime(to_date_time, "%Y-%m-%dT%H:%M")
    charge_per_hour = request.form.get("charge_per_hour")
    hours = request.form.get("hours")
    vehicle_title = request.form.get("vehicle_title")
    vehicle_number = request.form.get("vehicle_number")
    vehicle_type = request.form.get("vehicle_type")
    total_price = request.form.get("total_price")
    card_type = request.form.get("card_type")
    card_holder_name = request.form.get("card_holder_name")
    card_number = request.form.get("card_number")
    expiry_date = request.form.get("expiry_date")
    cvv = request.form.get("cvv")
    vehicle_model = request.form.get("vehicle_model")
    customer_id = session['customer_id']
    date = datetime.datetime.now()
    query = {"parking_slot_id": ObjectId(parking_slot_id), "customer_id": ObjectId(customer_id), "vehicle_model":vehicle_model, "vehicle_title": vehicle_title, "vehicle_number": vehicle_number, "vehicle_type": vehicle_type, "booking_date": date, "from_date_time": from_date_time, "to_date_time": to_date_time, "payable_amount": total_price, "status": 'Slot Booked'}
    result = reservation_collection.insert_one(query)
    reservation_id = result.inserted_id
    query = {"reservation_id": ObjectId(reservation_id), "customer_id": ObjectId(customer_id),
             "payment_date": date, "payment_method": card_type, "card_holder_name": card_holder_name,
             "card_number": card_number, "expiry_date": expiry_date, "cvv": cvv, "payable_amount": total_price, "status": 'Paid'}
    payment_details_collection.insert_one(query)
    return render_template("customer_message.html", message="Successfully Booked Parking Slot")


def is_slot_reserved(parking_slot_id, slot_number, from_date_time, to_date_time):
    # from_date_time = datetime.datetime.strptime(str(from_date_time), "%Y-%m-%d %H:%M:%S")
    # to_date_time = datetime.datetime.strptime(str(to_date_time), "%Y-%m-%d %H:%M:%S")
    query = {"$or": [{"from_date_time": {"$gte": from_date_time, "$lte": to_date_time}, "to_date_time": {"$gte": from_date_time, "$gte": to_date_time}, "status": {"$nin": ['Cancelled', 'Vacated']}, "parking_slot_id": ObjectId(parking_slot_id), "slot_number": str(slot_number)},
                     {"from_date_time": {"$lte": from_date_time, "$lte": to_date_time}, "to_date_time": {"$gte": from_date_time, "$lte": to_date_time}, "status": {"$nin": ['Cancelled', 'Vacated']}, "parking_slot_id": ObjectId(parking_slot_id), "slot_number": str(slot_number)},
                     {"from_date_time": {"$lte": from_date_time, "$lte": to_date_time}, "to_date_time": {"$gte": from_date_time, "$gte": to_date_time}, "status": {"$nin": ['Cancelled', 'Vacated']}, "parking_slot_id": ObjectId(parking_slot_id), "slot_number": str(slot_number)},
                     {"from_date_time": {"$gte": from_date_time, "$lte": to_date_time},"to_date_time": {"$gte": from_date_time, "$lte": to_date_time}, "status": {"$nin": ['Cancelled', 'Vacated']}, "parking_slot_id": ObjectId(parking_slot_id), "slot_number": str(slot_number)},
                     ]}
    count = reservation_collection.count_documents(query)
    if count > 0:
        return True
    else:
        return False

@app.route("/view_booking")
def view_booking():
    role = session['role']
    query = {}
    if role == 'customer':
        customer_id = session['customer_id']
        reservations = reservation_collection.find({"customer_id": ObjectId(customer_id)})
    elif role == 'admin':
        reservations = reservation_collection.find()
    return render_template("view_booking.html", timer_show=timer_show, count=count, get_is_parking_time_out=get_is_parking_time_out,get_ratings_by_id=get_ratings_by_id, reservations=reservations, get_customer_by_customer_id=get_customer_by_customer_id, get_parking_slot_by_parking_slot_id=get_parking_slot_by_parking_slot_id, get_parking_location_by_parking_location_id=get_parking_location_by_parking_location_id, int=int, is_slot_reserved=is_slot_reserved)


def get_ratings_by_id(parking_slot_id):
    reservations = reservation_collection.find({"parking_slot_id": ObjectId(parking_slot_id)})
    reservationIds = []
    for booking in reservations:
        reservationIds.append(booking['_id'])
    totalRating = 0
    count = 0
    query = {"reservation_id": {"$in": reservationIds}}
    reviews = review_collection.find(query)
    if reviews != None:
        for review in reviews:
            totalRating = totalRating + int(review['rating'])
            count = count + 1
        if count > 0:
            rating = (totalRating / count)
        else:
            rating = "No Ratings"
        return rating
    else:
        return "No Ratings"


@app.route("/pay_amount")
def pay_amount():
    query =  {}
    pay_amount = payment_details_collection.find(query)
    pay_amount = list(pay_amount)
    return render_template("pay_amount.html", pay_amount=pay_amount)


def get_parking_slot_by_parking_slot_id(parking_slot_id):
    parking_slot = parking_slot_collection.find_one({"_id": ObjectId(parking_slot_id)})
    return parking_slot


def get_customer_by_customer_id(customer_id):
    customer = customer_collection.find_one({"_id": ObjectId(customer_id)})
    return customer


def get_parking_location_by_parking_location_id(parking_location_id):
    parking_location = parking_location_collection.find_one({"_id": ObjectId(parking_location_id)})
    return parking_location


@app.route("/add_parking_location_action")
def add_parking_location_action():
    parking_area_name = request.args.get("parking_area_name")
    parking_location_id = request.args.get("parking_location_id")
    number_of_slots = request.args.get("number_of_slots")
    price_per_hour = request.args.get("price_per_hour")
    date = datetime.datetime.now()
    date = datetime.datetime.strftime(date, "%Y-%m-%d %H:%M")
    query = {"parking_location_id": ObjectId(parking_location_id), "parking_area_name": parking_area_name, "number_of_slots": number_of_slots,
             "datetime": date, "price_per_hour": price_per_hour, "status": 'Available'}
    parking_slot_collection.insert_one(query)
    return render_template("admin_message.html", message="Added Parking Slots Successful")


@app.route("/update_status")
def update_status():
    reservation_id = request.args.get("reservation_id")
    status = request.args.get("status")
    query1 = {"_id": ObjectId(reservation_id)}
    query2 = {"$set": {"status": status}}
    reservation_collection.update_one(query1, query2)
    query3 = {"$set": {"status": 'Refunded'}}
    payment_details_collection.update_one(query1, query3)
    return redirect("/view_booking")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/view_payment")
def view_payment():
    reservation_id = request.args.get("reservation_id")
    reservation = reservation_collection.find_one({"_id": ObjectId(reservation_id)})
    customer_id = reservation['customer_id']
    customer = customer_collection.find_one({"_id": ObjectId(customer_id)})
    query = {"reservation_id": ObjectId(reservation_id), "customer_id": ObjectId(customer_id)}
    payment_details = payment_details_collection.find_one(query)
    return render_template("view_payment.html", payment_details=payment_details, customer=customer)


def get_booked_slots_count(parking_slot_id, from_date_time, to_date_time):
    print(from_date_time)
    from_date_time = datetime.datetime.strptime(from_date_time, "%Y-%m-%dT%H:%M")
    to_date_time = datetime.datetime.strptime(to_date_time, "%Y-%m-%dT%H:%M")
    query = {"$or": [{"from_date_time": {"$gte": from_date_time, "$lte": to_date_time},
                      "to_date_time": {"$gte": from_date_time, "$gte": to_date_time},
                      "status": {"$nin": ['Cancelled', 'Vacated']}, "parking_slot_id": ObjectId(parking_slot_id)},
                     {"from_date_time": {"$lte": from_date_time, "$lte": to_date_time},
                      "to_date_time": {"$gte": from_date_time, "$lte": to_date_time},
                      "status": {"$nin": ['Cancelled', 'Vacated']}, "parking_slot_id": ObjectId(parking_slot_id)},
                     {"from_date_time": {"$lte": from_date_time, "$lte": to_date_time},
                      "to_date_time": {"$gte": from_date_time, "$gte": to_date_time},
                      "status": {"$nin": ['Cancelled', 'Vacated']}, "parking_slot_id": ObjectId(parking_slot_id)},
                     {"from_date_time": {"$gte": from_date_time, "$lte": to_date_time},
                      "to_date_time": {"$gte": from_date_time, "$lte": to_date_time},
                      "status": {"$nin": ['Cancelled', 'Vacated']}, "parking_slot_id": ObjectId(parking_slot_id)},
                     ]}
    count = reservation_collection.count_documents(query)
    return count


@app.route("/update_slot_number")
def update_slot_number():
    reservation_id = request.args.get("reservation_id")
    slot_number = request.args.get("slot_number")
    print(reservation_id)
    print(slot_number)
    query1 = {"_id": ObjectId(reservation_id)}
    query2 = {"$set": {"slot_number": slot_number, "status": 'Checked in'}}
    reservation_collection.update_one(query1, query2)
    return redirect("/view_booking")


@app.route("/extend_slot_time")
def extend_slot_time():
    reservation_id = request.args.get("reservation_id")
    reservation = reservation_collection.find_one({"_id": ObjectId(reservation_id)})
    to_date_time1 = reservation['to_date_time']
    from_date_time = request.args.get('from_date_time')
    to_date_time = request.args.get('to_date_time')
    if from_date_time == None:
        from_date_time = to_date_time1
        to_date_time = from_date_time + datetime.timedelta(minutes=60)
        from_date_time = from_date_time.strftime("%Y-%m-%dT%H:%M")
        to_date_time = to_date_time.strftime("%Y-%m-%dT%H:%M")
    return render_template("extend_slot_time.html", to_date_time=to_date_time, from_date_time=from_date_time, reservation_id=reservation_id)


@app.route("/extend_slot_time1")
def extend_slot_time1():
    reservation_id = request.args.get("reservation_id")
    payment = payment_details_collection.find_one({"reservation_id": ObjectId(reservation_id)})
    from_date_time = request.args.get("from_date_time")
    to_date_time = request.args.get("to_date_time")
    from_date_time2 = datetime.datetime.strptime(from_date_time, "%Y-%m-%dT%H:%M")
    to_date_time2 = datetime.datetime.strptime(to_date_time, "%Y-%m-%dT%H:%M")
    reservation = reservation_collection.find_one({"_id": ObjectId(reservation_id)})
    parking_slot_id = reservation['parking_slot_id']
    parking_slot = parking_slot_collection.find_one({"_id": ObjectId(parking_slot_id)})
    price_per_hour = parking_slot['price_per_hour']
    diff = to_date_time2 - from_date_time2
    days = diff.days
    seconds = diff.seconds
    hours = seconds/3600
    if seconds % 3600 > 0:
        hours = hours + 1
    hours = hours + days * 24
    hours = int(hours)
    total_price = int(parking_slot['price_per_hour'])*hours
    return render_template("extend_slot_time1.html", payment=payment, reservation=reservation, reservation_id=reservation_id, parking_slot_id=parking_slot_id,from_date_time=from_date_time, to_date_time=to_date_time, hours=hours, total_price=total_price, parking_slot=parking_slot, price_per_hour=price_per_hour)


@app.route("/update_time_extended")
def update_time_extended():
    reservation_id = request.args.get("reservation_id")
    to_date_time1 = request.args.get("to_date_time")
    to_date_time = datetime.datetime.strptime(to_date_time1, "%Y-%m-%dT%H:%M")
    total_price = request.args.get("total_price")
    reservation = reservation_collection.find_one({"_id": ObjectId(reservation_id)})
    payable_amount1 = reservation['payable_amount']
    payable_amount = int(payable_amount1)+int(total_price)
    query1 = {"_id": ObjectId(reservation_id)}
    query2 = {"$set": {"payable_amount": payable_amount, "to_date_time": to_date_time}}
    reservation_collection.update_one(query1, query2)
    return redirect("/view_booking")


@app.route("/add_review")
def add_review():
    reservation_id = request.args.get("reservation_id")
    return render_template("add_review.html", reservation_id=reservation_id)


@app.route("/add_review1", methods=['post'])
def add_review1():
    reservation_id = request.form.get("reservation_id")
    review = request.form.get("review")
    rating = request.form.get("rating")
    date = datetime.datetime.now()
    date = datetime.datetime.strftime(date, "%Y-%m-%d %H:%M")
    query = {"review": review, "rating": rating, "reservation_id": ObjectId(reservation_id), "date": date}
    review_collection.insert_one(query)
    query1 = {"_id": ObjectId(reservation_id)}
    query2 = {"$set": {"status": 'Review Given'}}
    reservation_collection.update_one(query1, query2)
    return redirect("/view_booking")


@app.route("/view_review")
def view_review():
    reservation_id = request.args.get("reservation_id")
    review = review_collection.find_one({"reservation_id": ObjectId(reservation_id)})
    return render_template("view_review.html", review=review)


@app.route("/ratings")
def ratings():
    parking_slot_id = request.args.get("parking_slot_id")
    reservations = reservation_collection.find({"parking_slot_id": ObjectId(parking_slot_id)})
    totalRating = 0
    count = 0
    reviewList = []
    for reservation in reservations:
        query4 = {"reservation_id": ObjectId(reservation['_id'])}
        r = review_collection.find_one(query4)
        if r != None:
            reviewList.append(r)
            totalRating = totalRating + int(r['rating'])
            count = count + 1
    if count > 0:
        rating = float(totalRating / count)
    else:
        rating = 0
    list.reverse(reviewList)
    return render_template("ratings.html",rating=rating,reviewList=reviewList,get_customer_by_id2=get_customer_by_id2, str=str)


def get_customer_by_id2(reservation_id):
    reservation = reservation_collection.find_one({"_id": ObjectId(reservation_id)})
    customer_id = reservation['customer_id']
    customer = (customer_collection.find_one({"_id": ObjectId(customer_id)}))
    return customer


def get_is_parking_time_out(solt_ending_time, reservation_id):
    solt_ending_time = datetime.datetime.strptime(str(solt_ending_time), "%Y-%m-%d %H:%M:%S")
    today = datetime.datetime.now()
    today = today.strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.datetime.strptime(str(today), "%Y-%m-%d %H:%M:%S")
    print(solt_ending_time,today)
    diff = solt_ending_time-today
    days, seconds = diff.days, diff.seconds
    hours = days * 24 + seconds // 3600
    if hours == 1:
        reservation = reservation_collection.find_one({"_id":ObjectId(reservation_id)})
        customer_id = reservation['customer_id']
        print(customer_id)
        customer = customer_collection.find_one({"_id":ObjectId(customer_id)})
        print(customer)
        name = customer['first_name']
        send_email("","Hello Your slot booking time is going to end in next 1 hour.", customer['email'])
    return "hello"


def timer_show(reservation_id):
    query = {"_id": ObjectId(reservation_id)}
    reservation = reservation_collection.find_one(query)
    to_date = reservation['to_date_time']
    current_date = datetime.datetime.now()
    # current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    diff = to_date - current_date
    hour_difference = diff.total_seconds() / 3600
    second_difference = diff.total_seconds() / 60
    second_difference = int(second_difference)
    print(second_difference,'balaji')
    # if second_difference*60 >3600:
    #     return 0
    return second_difference

app.run(debug=True)

