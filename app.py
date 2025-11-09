import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import datetime

# --- TINYPNG AND DOTENV IMPORTS ---
import tinify
from dotenv import load_dotenv

# --- LOAD ENVIRONMENT VARIABLES AND CONFIGURE TINYPNG ---
load_dotenv() # Load variables from the .env file
tinify.key = os.getenv('TINYPNG_API_KEY') # Set your API key

# --- IMAGE OPTIMIZATION FUNCTION USING TINYPNG ---
def optimize_with_tinypng(file_storage, output_path, max_width=1920, max_height=None):
    """
    Optimizes an uploaded image using the TinyPNG API: resizes, converts to WebP, and saves it.
    Returns the new filename.
    """
    # Ensure file_storage is not empty
    if not file_storage or file_storage.filename == '':
        return None

    filename_base = os.path.splitext(secure_filename(file_storage.filename))[0]
    new_filename = f"{filename_base}.webp"
    save_path = os.path.join(output_path, new_filename)

    try:
        print(f"Optimizing {file_storage.filename} with TinyPNG...")
        image_data = file_storage.read()
        source = tinify.from_buffer(image_data)
        
        # Determine resize method
        if max_width and max_height:
            resized = source.resize(method="fit", width=max_width, height=max_height)
        elif max_width:
            resized = source.resize(method="scale", width=max_width)
        elif max_height:
            resized = source.resize(method="scale", height=max_height)
        else:
            resized = source # No resize, just convert

        converted = resized.convert(type=["image/webp"])
        
        converted.to_file(save_path)
        
        print(f"Successfully optimized and saved as {new_filename}")
        return new_filename

    except tinify.Error as e:
        print(f"TinyPNG API Error: {e.message}")
        flash(f"Image optimization failed: {e.message}. Attempting to save original file.", "warning")
        original_filename = secure_filename(file_storage.filename)
        file_storage.seek(0) # Reset file pointer after reading for tinify
        file_storage.save(os.path.join(output_path, original_filename))
        return original_filename
    except Exception as e:
        print(f"A general error occurred during image processing: {e}")
        flash(f"An unexpected error occurred during image processing: {e}", "danger")
        return None

# --- APP CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_for_marogo_civils'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'marogo.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
try:
    os.makedirs(app.instance_path)
    os.makedirs(app.config['UPLOAD_FOLDER'])
except OSError:
    pass
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    client = db.Column(db.String(100))
    location = db.Column(db.String(100))
    project_value = db.Column(db.String(50))
    completion_date = db.Column(db.String(50))
    details = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(50), nullable=False, default='General Construction')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    images = db.relationship('ProjectImage', backref='project', lazy=True, cascade="all, delete-orphan")

class ProjectImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(200), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    image_url = db.Column(db.String(200), nullable=True) # For the service thumbnail image (replaces icon_class)
    summary = db.Column(db.String(255), nullable=False)
    full_content = db.Column(db.Text, nullable=False)
    order_num = db.Column(db.Integer, default=0)
    header_image_url = db.Column(db.String(200), nullable=True) # For the service detail page banner
    project_category_link = db.Column(db.String(50), nullable=True) # E.g., 'Building Construction'


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False, default='Admin')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=True)
    quote = db.Column(db.Text, nullable=False)

class ContactSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    submitted_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Statistic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Integer, nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    order_num = db.Column(db.Integer, default=0)

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=False)
    order_num = db.Column(db.Integer, default=0)

class ClientLogo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    website_url = db.Column(db.String(200), nullable=True)
    order_num = db.Column(db.Integer, default=0)

class Certification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    issuing_body = db.Column(db.String(200), nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    order_num = db.Column(db.Integer, default=0)

# FA_ICONS are needed for Statistics (and possibly others), but not for Services/Certifications anymore
FA_ICONS = [
    {'class': 'fas fa-hard-hat', 'name': 'Hard Hat (Construction)'},
    {'class': 'fas fa-tools', 'name': 'Tools'},
    {'class': 'fas fa-hammer', 'name': 'Hammer'},
    {'class': 'fas fa-wrench', 'name': 'Wrench'},
    {'class': 'fas fa-drafting-compass', 'name': 'Drafting Compass'},
    {'class': 'fas fa-solar-panel', 'name': 'Solar Panel'},
    {'class': 'fas fa-water', 'name': 'Water / Irrigation'},
    {'class': 'fas fa-road', 'name': 'Road'},
    {'class': 'fas fa-truck-loading', 'name': 'Materials Supply'},
    {'class': 'fas fa-tint', 'name': 'Water Drop (Borehole)'},
    {'class': 'fas fa-award', 'name': 'Award / Quality'},
    {'class': 'fas fa-users', 'name': 'Happy Clients'},
    {'class': 'fas fa-handshake', 'name': 'Handshake / Partnership'},
    {'class': 'fas fa-chart-line', 'name': 'Growth Chart'},
    {'class': 'fas fa-star', 'name': 'Star / Rating'},
    {'class': 'fas fa-user-shield', 'name': 'Safety / Shield'},
    {'class': 'fas fa-building', 'name': 'Building'},
    {'class': 'fas fa-clock', 'name': 'Clock / On Time'},
    {'class': 'fas fa-check-circle', 'name': 'Check Circle (Certified)'}
]

# --- Define Project Categories (for Service linking) ---
# This list MUST match the 'value' attributes in your manage_content.html for projects
PROJECT_CATEGORIES = [
    "Building Construction",
    "Solar Systems",
    "Irrigation",           # This is the 'value' in the <option>
    "Drainage",             # This is the 'value' in the <option>
    "Surveying",            # This is the 'value' in the <option>
    "Fabrication",          # This is the 'value' in the <option>
    "General Construction"
]


# --- DECORATORS & CONTEXT ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow()}

@app.context_processor
def inject_project_categories(): # Make project categories available to all templates
    return {'project_categories': PROJECT_CATEGORIES}

# --- FILE SERVING ROUTE ---
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- FRONTEND ROUTES ---
@app.route('/')
def home():
    projects = Project.query.order_by(Project.date_posted.desc()).limit(4).all()
    blog_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(3).all()
    testimonials = Testimonial.query.all()
    statistics = Statistic.query.order_by(Statistic.order_num.asc()).all()
    client_logos = ClientLogo.query.order_by(ClientLogo.order_num.asc()).all()
    return render_template('index.html', projects=projects, blog_posts=blog_posts,
                           testimonials=testimonials, statistics=statistics,
                           client_logos=client_logos)

@app.route('/about')
def about():
    team_members = TeamMember.query.order_by(TeamMember.order_num.asc()).all()
    certifications = Certification.query.order_by(Certification.order_num.asc()).all()
    return render_template('about.html', team_members=team_members, certifications=certifications)

@app.route('/services')
def services():
    all_services = Service.query.order_by(Service.order_num.asc()).all()
    return render_template('services.html', services=all_services)

@app.route('/service/<slug>')
def service_detail(slug):
    service = Service.query.filter_by(slug=slug).first_or_404()
    
    # --- UPDATED Logic: Use service.project_category_link directly ---
    # Fallback to service.title if project_category_link is not set, BUT prefer the link
    search_category = service.project_category_link if service.project_category_link else service.title
    
    related_projects = Project.query.filter(
        Project.category.ilike(f'%{search_category}%') # Case-insensitive partial match
    ).order_by(Project.date_posted.desc()).limit(3).all()

    return render_template('service_detail.html', service=service, related_projects=related_projects)

@app.route('/projects')
def projects():
    all_projects = Project.query.order_by(Project.date_posted.desc()).all()
    return render_template('projects.html', projects=all_projects)

@app.route('/blog')
def blog():
    all_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    return render_template('blog.html', blog_posts=all_posts)

@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('blog_post.html', post=post)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name, email, subject, message = request.form['name'], request.form['email'], request.form['subject'], request.form['message']
        new_submission = ContactSubmission(name=name, email=email, subject=subject, message=message)
        db.session.add(new_submission)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Thank you! Your message has been sent successfully.'})
    return render_template('contact.html')

# --- ADMIN ROUTES ---
@app.route('/admin')
def admin_redirect(): return redirect(url_for('dashboard'))

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            session['user_id'], session['username'] = user.id, user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
def dashboard():
    stats = {
        'projects': Project.query.count(),
        'posts': BlogPost.query.count(),
        'testimonials': Testimonial.query.count(),
        'submissions': ContactSubmission.query.count(),
        'statistics': Statistic.query.count(),
        'team_members': TeamMember.query.count(),
        'services': Service.query.count(),
        'client_logos': ClientLogo.query.count(),
        'certifications': Certification.query.count()
    }
    submissions = ContactSubmission.query.order_by(ContactSubmission.submitted_on.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, submissions=submissions)

@app.route('/admin/submissions/<int:submission_id>')
@login_required
def view_submission(submission_id):
    submission = ContactSubmission.query.get_or_404(submission_id)
    return render_template('admin/view_submission.html', submission=submission)


@app.route('/admin/edit/<content_type>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_content(content_type, item_id):
    models = {
        'projects': Project, 'blog': BlogPost, 'testimonials': Testimonial,
        'statistics': Statistic, 'team_members': TeamMember, 'services': Service,
        'client_logos': ClientLogo, 'certifications': Certification
    }
    Model = models.get(content_type)
    if not Model:
        flash('Invalid content type.', 'danger')
        return redirect(url_for('dashboard'))
    item = Model.query.get_or_404(item_id)
    
    if request.method == 'POST':
        if content_type == 'projects':
            item.title = request.form['title']
            item.client = request.form.get('client')
            item.location = request.form.get('location')
            item.project_value = request.form.get('project_value')
            item.completion_date = request.form.get('completion_date')
            item.details = request.form['details']
            item.category = request.form['category']
            if 'project_image' in request.files:
                file = request.files['project_image']
                if file and file.filename != '':
                    filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'])
                    if filename: item.image_url = filename
            if 'gallery_images' in request.files:
                files = request.files.getlist('gallery_images')
                for file in files:
                    if file and file.filename != '':
                        filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'], max_width=1200)
                        if filename:
                            new_image = ProjectImage(image_url=filename, project_id=item.id)
                            db.session.add(new_image)
            if 'delete_images' in request.form:
                images_to_delete_ids = request.form.getlist('delete_images')
                for img_id in images_to_delete_ids:
                    image_to_delete = ProjectImage.query.get(img_id)
                    if image_to_delete:
                        try:
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_to_delete.image_url))
                        except OSError as e:
                            print(f"Error deleting file {image_to_delete.image_url}: {e}")
                        db.session.delete(image_to_delete)
        elif content_type == 'blog':
            item.title = request.form['title']
            item.content = request.form['content']
        elif content_type == 'testimonials':
            item.author = request.form['author']
            item.position = request.form.get('position', '')
            item.quote = request.form['quote']
        elif content_type == 'statistics':
            item.name = request.form['name']
            item.value = int(request.form['value'])
            item.icon = request.form['icon']
            item.order_num = int(request.form['order_num'])
        elif content_type == 'team_members':
            item.name = request.form['name']
            item.position = request.form['position']
            item.bio = request.form['bio']
            item.order_num = int(request.form['order_num'])
            if 'member_image' in request.files:
                file = request.files['member_image']
                if file and file.filename != '':
                    filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'], max_width=800)
                    if filename: item.image_url = filename
        elif content_type == 'services':
            item.title = request.form['title']
            item.slug = request.form['title'].lower().replace(' ', '-').replace('&', 'and').replace('/', '_')
            item.summary = request.form['summary']
            item.full_content = request.form['full_content']
            item.order_num = int(request.form['order_num'])
            item.project_category_link = request.form.get('project_category_link') # NEW

            # --- Handle service thumbnail image update ---
            if 'service_thumbnail_image' in request.files:
                file = request.files['service_thumbnail_image']
                if file and file.filename != '':
                    if item.image_url:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_url)
                        if os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                                print(f"Deleted old service thumbnail image: {item.image_url}")
                            except OSError as e:
                                print(f"Error deleting old service thumbnail image {item.image_url}: {e}")
                    filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'], max_width=150, max_height=150)
                    if filename: item.image_url = filename
            # --- Handle service header image update ---
            if 'service_header_image' in request.files:
                file = request.files['service_header_image']
                if file and file.filename != '':
                    if item.header_image_url:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.header_image_url)
                        if os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                                print(f"Deleted old service header image: {item.header_image_url}")
                            except OSError as e:
                                print(f"Error deleting old service header image {item.header_image_url}: {e}")
                    filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'], max_width=1920)
                    if filename: item.header_image_url = filename
        elif content_type == 'certifications':
            item.name = request.form['name']
            item.issuing_body = request.form.get('issuing_body', '')
            item.order_num = int(request.form['order_num'])
            if 'certification_image' in request.files:
                file = request.files['certification_image']
                if file and file.filename != '':
                    if item.image_url:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_url)
                        if os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                                print(f"Error deleting old certification image: {item.image_url}")
                            except OSError as e:
                                print(f"Error deleting old certification image {item.image_url}: {e}")
                    filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'], max_width=200, max_height=200) 
                    if filename: item.image_url = filename
        
        db.session.commit()
        flash(f'{content_type.replace("_", " ").title()[:-1]} updated successfully!', 'success')
        return redirect(url_for('manage_content', content_type=content_type))
    
    if content_type == 'statistics':
        return render_template('admin/edit_content.html', content_type=content_type, item=item, fa_icons=FA_ICONS)
    # project_categories is available globally via context_processor.
    return render_template('admin/edit_content.html', content_type=content_type, item=item)

@app.route('/admin/manage/<content_type>', methods=['GET', 'POST'])
@login_required
def manage_content(content_type):
    models = {
        'projects': Project, 'blog': BlogPost, 'testimonials': Testimonial,
        'statistics': Statistic, 'team_members': TeamMember, 'services': Service,
        'client_logos': ClientLogo, 'certifications': Certification
    }
    Model = models.get(content_type)
    if not Model:
        flash('Invalid content type.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        if content_type == 'projects':
            if 'project_image' not in request.files or request.files['project_image'].filename == '':
                flash('An image file is required for the project.', 'danger')
                return redirect(request.url)
            file = request.files['project_image']
            filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'])
            if filename:
                new_item = Model(title=request.form['title'], client=request.form.get('client'), location=request.form.get('location'), project_value=request.form.get('project_value'), completion_date=request.form.get('completion_date'), details=request.form['details'], category=request.form['category'], image_url=filename)
        elif content_type == 'blog':
            new_item = Model(title=request.form['title'], content=request.form['content'])
        elif content_type == 'testimonials':
            new_item = Model(author=request.form['author'], position=request.form.get('position', ''), quote=request.form['quote'])
        elif content_type == 'statistics':
            new_item = Model(name=request.form['name'], value=int(request.form['value']), icon=request.form['icon'], order_num=int(request.form['order_num']))
        elif content_type == 'team_members':
            if 'member_image' not in request.files or request.files['member_image'].filename == '':
                flash('An image file is required for the team member.', 'danger')
                return redirect(request.url)
            file = request.files['member_image']
            filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'], max_width=800)
            if filename:
                new_item = Model(name=request.form['name'], position=request.form['position'], bio=request.form['bio'], image_url=filename, order_num=int(request.form['order_num']))
        elif content_type == 'services':
            service_title = request.form['title']
            service_slug = service_title.lower().replace(' ', '-').replace('&', 'and').replace('/', '_')
            
            # --- Handle new service thumbnail image upload ---
            thumbnail_image_filename = None
            if 'service_thumbnail_image' not in request.files or request.files['service_thumbnail_image'].filename == '':
                flash('A service thumbnail image is required.', 'danger')
                return redirect(request.url)
            file = request.files['service_thumbnail_image']
            thumbnail_image_filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'], max_width=150, max_height=150)

            # --- Handle new service header image upload (optional for add form) ---
            header_image_filename = None
            if 'service_header_image' in request.files: 
                file = request.files['service_header_image']
                if file and file.filename != '':
                    header_image_filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'], max_width=1920)

            new_item = Model(
                title=service_title,
                slug=service_slug,
                image_url=thumbnail_image_filename,
                summary=request.form['summary'],
                full_content=request.form['full_content'],
                order_num=int(request.form['order_num']),
                header_image_url=header_image_filename,
                project_category_link=request.form.get('project_category_link') # NEW
            )
        elif content_type == 'client_logos':
            if 'logo_image' not in request.files or request.files['logo_image'].filename == '':
                flash('An image file is required for the client logo.', 'danger')
                return redirect(request.url)
            file = request.files['logo_image']
            filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'], max_width=400)
            if filename:
                new_item = Model(name=request.form['name'], website_url=request.form.get('website_url', ''), image_url=filename, order_num=int(request.form['order_num']))
        elif content_type == 'certifications':
            if 'certification_image' not in request.files or request.files['certification_image'].filename == '':
                flash('A certification image file is required.', 'danger')
                return redirect(request.url)
            file = request.files['certification_image']
            filename = optimize_with_tinypng(file, app.config['UPLOAD_FOLDER'], max_width=200, max_height=200)
            if filename:
                new_item = Model(
                    name=request.form['name'], 
                    issuing_body=request.form.get('issuing_body', ''), 
                    image_url=filename,
                    order_num=int(request.form['order_num'])
                )
            else:
                flash('Failed to upload certification image.', 'danger')
                return redirect(request.url)

        if 'new_item' in locals():
            db.session.add(new_item)
            db.session.commit()
            flash(f'{content_type.replace("_", " ").title()[:-1]} added successfully!', 'success')
        return redirect(url_for('manage_content', content_type=content_type))

    if content_type in ['statistics', 'team_members', 'services', 'client_logos', 'certifications']:
        items = Model.query.order_by(Model.order_num.asc()).all()
    else:
        items = Model.query.order_by(Model.id.desc()).all()

    if content_type == 'statistics':
        return render_template('admin/manage_content.html', content_type=content_type, items=items, fa_icons=FA_ICONS)
    return render_template('admin/manage_content.html', content_type=content_type, items=items)

@app.route('/admin/delete/<content_type>/<int:item_id>', methods=['POST'])
@login_required
def delete_content(content_type, item_id):
    models = {
        'projects': Project, 'blog': BlogPost, 'testimonials': Testimonial,
        'submissions': ContactSubmission, 'statistics': Statistic, 'team_members': TeamMember,
        'services': Service, 'client_logos': ClientLogo, 'certifications': Certification
    }
    Model = models.get(content_type)
    if not Model: return "Invalid content type", 404
    item = Model.query.get_or_404(item_id)

    # Delete associated files from uploads folder
    if hasattr(item, 'image_url') and item.image_url:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.image_url))
        except OSError as e:
            print(f"Error deleting file {item.image_url}: {e}")
    if content_type == 'projects' and hasattr(item, 'images'):
        for img in item.images:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img.image_url))
            except OSError as e:
                print(f"Error deleting gallery file {img.image_url}: {e}")
    if content_type == 'services' and hasattr(item, 'header_image_url') and item.header_image_url:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.header_image_url))
        except OSError as e:
            print(f"Error deleting service header image {item.header_image_url}: {e}")

    db.session.delete(item)
    db.session.commit()
    flash(f'{content_type.replace("_", " ").title()[:-1]} deleted.', 'info')
    if content_type == 'submissions':
        return redirect(url_for('dashboard'))
    return redirect(url_for('manage_content', content_type=content_type))

if __name__ == '__main__':
    # It's good practice to ensure the instance folder and uploads folder exist before app.run
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError as e:
        print(f"Error creating instance or uploads directory: {e}")
    app.run(debug=True)