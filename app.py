from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import qrcode
from io import BytesIO
import base64
import random
import nltk
from nltk.corpus import wordnet

# Download NLTK resources (only required once)
nltk.download("wordnet")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'supersecretkey'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# 📌 User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# 📌 Business Model
class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    website = db.Column(db.String(200), nullable=False)

# 📌 Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# 📌 Add Business
@app.route("/add_business", methods=["GET", "POST"])
@login_required
def add_business():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        website = request.form["website"]
        new_business = Business(name=name, description=description, website=website)
        db.session.add(new_business)
        db.session.commit()
        flash("Business added successfully!", "success")
    return render_template("add_business.html")

# 📌 Add Product
@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = float(request.form["price"])
        new_product = Product(name=name, description=description, price=price)
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully!", "success")
    return render_template("add_product.html")

# 📌 View Business List
@app.route("/business_list")
@login_required
def business_list():
    businesses = Business.query.all()
    return render_template("business_list.html", businesses=businesses)

# 📌 View Product List
@app.route("/product_list")
@login_required
def product_list():
    products = Product.query.all()
    return render_template("product_list.html", products=products)

# 📌 Delete Business
@app.route("/delete_business/<int:business_id>", methods=["POST"])
@login_required
def delete_business(business_id):
    business = Business.query.get_or_404(business_id)
    db.session.delete(business)
    db.session.commit()
    flash("Business deleted successfully!", "success")
    return redirect(url_for("business_list"))

# 📌 Delete Product
@app.route("/delete_product/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully!", "success")
    return redirect(url_for("product_list"))

# 📌 QR Code Generator
@app.route("/qr_generator", methods=["GET", "POST"])
@login_required
def qr_generator():
    qr_code = None
    if request.method == "POST":
        url = request.form["website"]
        qr = qrcode.make(url)
        buffered = BytesIO()
        qr.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return render_template("qr_generator.html", qr_code=qr_code)

# 📌 Dynamic Company Name Generator
def generate_company_names(keyword):
    keyword = keyword.strip().title()
    synonyms = set()

    # Get synonyms from WordNet
    for syn in wordnet.synsets(keyword.lower()):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().title())

    synonyms_list = sorted(list(synonyms))

    company_names = set()

    # Generate unique names using combinations of synonyms
    if len(synonyms_list) > 1:
        for _ in range(min(5, len(synonyms_list) - 1)):  
            name = f"{random.choice(synonyms_list)} {random.choice(synonyms_list)}"
            if name.split()[0] != name.split()[1]:  # Avoid duplicate words
                company_names.add(name)
    else:
        company_names.add(keyword)  # If no synonyms, use the original word

    return list(company_names)

@app.route("/generate_company_names", methods=["GET", "POST"])
def generate_company_names_page():
    company_names = set()

    if request.method == "POST":
        keywords = request.form["keywords"].split(",")
        keywords = set(keyword.strip().lower() for keyword in keywords if keyword.strip())

        for keyword in keywords:
            company_names.update(generate_company_names(keyword))

    return render_template("generate_company_names.html", company_names=company_names)

# 📌 Smart Hashtag Generator using NLP (WordNet)
def generate_smart_hashtags(keyword):
    keyword = keyword.strip().replace(" ", "_")  
    hashtags = [f"#{keyword}"]  
    
    synonyms = set()
    for syn in wordnet.synsets(keyword):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().replace("_", "").title())  

    synonyms_list = sorted(list(synonyms))  

    if len(synonyms_list) > 0:
        related_tags = random.sample(synonyms_list, min(3, len(synonyms_list)))
        for tag in related_tags:
            hashtags.append(f"#{tag}")

    return hashtags

@app.route("/generate_hashtags", methods=["GET", "POST"])
def generate_hashtags():
    hashtags = set()
    if request.method == "POST":
        keywords = request.form["keywords"].split(",")
        keywords = set(keyword.strip().lower() for keyword in keywords if keyword.strip())  

        for keyword in keywords:
            hashtags.update(generate_smart_hashtags(keyword))  

    return render_template("generate_hashtags.html", hashtags=hashtags)

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)