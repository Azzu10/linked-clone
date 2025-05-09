from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a real secret key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///linkedin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define models
connections = db.Table('connections',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('connection_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    headline = db.Column(db.String(120))
    about = db.Column(db.Text)
    location = db.Column(db.String(120))
    profile_picture = db.Column(db.String(120), default='default_profile.jpg')
    background_image = db.Column(db.String(120), default='default_background.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    experiences = db.relationship('Experience', backref='user', lazy='dynamic')
    educations = db.relationship('Education', backref='user', lazy='dynamic')
    skills = db.relationship('Skill', backref='user', lazy='dynamic')
    
    connections_made = db.relationship(
        'User', secondary=connections,
        primaryjoin=(connections.c.user_id == id),
        secondaryjoin=(connections.c.connection_id == id),
        backref=db.backref('connected_to', lazy='dynamic'),
        lazy='dynamic'
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def connect(self, user):
        if not self.is_connected(user):
            self.connections_made.append(user)
            return self
            
    def disconnect(self, user):
        if self.is_connected(user):
            self.connections_made.remove(user)
            return self
            
    def is_connected(self, user):
        return self.connections_made.filter(connections.c.connection_id == user.id).count() > 0
        
    def get_connections(self):
        return self.connections_made.all()
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade="all, delete-orphan")

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('likes', lazy='dynamic'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))

class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school = db.Column(db.String(120), nullable=False)
    degree = db.Column(db.String(120))
    field_of_study = db.Column(db.String(120))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endorsements = db.Column(db.Integer, default=0)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120))
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    salary_range = db.Column(db.String(120))
    job_type = db.Column(db.String(64))  # Full-time, Part-time, Contract, etc.
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    poster = db.relationship('User', backref=db.backref('jobs_posted', lazy='dynamic'))
    applications = db.relationship('JobApplication', backref='job', lazy='dynamic', cascade="all, delete-orphan")

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resume = db.Column(db.String(120))
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(64), default='Applied')  # Applied, Reviewed, Interviewing, Rejected, Offered, Hired
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    applicant = db.relationship('User', backref=db.backref('job_applications', lazy='dynamic'))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('messages_sent', lazy='dynamic'))
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('messages_received', lazy='dynamic'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered')
            return redirect(url_for('register'))
        
        new_user = User(email=email, first_name=first_name, last_name=last_name)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful, please log in')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('feed'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/feed')
@login_required
def feed():
    # Get all connections
    connections = current_user.get_connections()
    connection_ids = [conn.id for conn in connections]
    connection_ids.append(current_user.id)  # Include own posts
    
    # Get posts from connections and self
    posts = Post.query.filter(Post.user_id.in_(connection_ids)).order_by(Post.created_at.desc()).all()
    
    # Get job recommendations (simplified)
    jobs = Job.query.order_by(Job.posted_at.desc()).limit(5).all()
    
    return render_template('feed.html', posts=posts, jobs=jobs)

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    experiences = Experience.query.filter_by(user_id=user.id).order_by(Experience.start_date.desc()).all()
    educations = Education.query.filter_by(user_id=user.id).order_by(Education.start_date.desc()).all()
    skills = Skill.query.filter_by(user_id=user.id).all()
    
    return render_template('profile.html', 
                           user=user, 
                           posts=posts, 
                           experiences=experiences, 
                           educations=educations,
                           skills=skills,
                           is_self=(user.id == current_user.id),
                           is_connected=current_user.is_connected(user))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Update basic info
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.headline = request.form.get('headline')
        current_user.about = request.form.get('about')
        current_user.location = request.form.get('location')
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                current_user.profile_picture = filename
        
        # Handle background image upload
        if 'background_image' in request.files:
            file = request.files['background_image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                current_user.background_image = filename
        
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('profile', user_id=current_user.id))
    
    return render_template('edit_profile.html', user=current_user)

@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content')
    
    if not content:
        flash('Post content cannot be empty')
        return redirect(url_for('feed'))
    
    new_post = Post(content=content, user_id=current_user.id)
    
    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            new_post.image = filename
    
    db.session.add(new_post)
    db.session.commit()
    
    flash('Post created successfully')
    return redirect(url_for('feed'))

@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if already liked
    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if like:
        # Unlike
        db.session.delete(like)
        action = 'unliked'
    else:
        # Like
        new_like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)
        action = 'liked'
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # For AJAX requests
        return jsonify({
            'action': action,
            'likes_count': post.likes.count()
        })
    else:
        # For regular form submissions
        return redirect(request.referrer or url_for('feed'))

@app.route('/comment_post/<int:post_id>', methods=['POST'])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty')
        return redirect(request.referrer or url_for('feed'))
    
    new_comment = Comment(content=content, user_id=current_user.id, post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # For AJAX requests
        return jsonify({
            'success': True,
            'comment_id': new_comment.id,
            'content': content,
            'author': current_user.get_full_name(),
            'created_at': new_comment.created_at.strftime('%B %d, %Y %H:%M')
        })
    else:
        # For regular form submissions
        return redirect(request.referrer or url_for('feed'))

@app.route('/connect/<int:user_id>', methods=['POST'])
@login_required
def connect(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot connect with yourself')
        return redirect(url_for('profile', user_id=user.id))
    
    if current_user.is_connected(user):
        current_user.disconnect(user)
        flash(f'You have disconnected from {user.get_full_name()}')
    else:
        current_user.connect(user)
        flash(f'You have connected with {user.get_full_name()}')
    
    db.session.commit()
    return redirect(url_for('profile', user_id=user.id))

@app.route('/connections')
@login_required
def connections():
    user_connections = current_user.get_connections()
    return render_template('connections.html', connections=user_connections)

@app.route('/jobs')
@login_required
def jobs():
    jobs = Job.query.order_by(Job.posted_at.desc()).all()
    return render_template('jobs.html', jobs=jobs)

@app.route('/job/<int:job_id>')
@login_required
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    already_applied = JobApplication.query.filter_by(job_id=job.id, applicant_id=current_user.id).first() is not None
    return render_template('job_details.html', job=job, already_applied=already_applied)

@app.route('/apply_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if already applied
    if JobApplication.query.filter_by(job_id=job.id, applicant_id=current_user.id).first():
        flash('You have already applied for this job')
        return redirect(url_for('job_details', job_id=job.id))
    
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter')
        
        application = JobApplication(
            job_id=job.id,
            applicant_id=current_user.id,
            cover_letter=cover_letter
        )
        
        # Handle resume upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                application.resume = filename
        
        db.session.add(application)
        db.session.commit()
        
        flash('Application submitted successfully')
        return redirect(url_for('jobs'))
    
    return render_template('apply_job.html', job=job)

@app.route('/post_job', methods=['GET', 'POST'])
@login_required
def post_job():
    if request.method == 'POST':
        title = request.form.get('title')
        company = request.form.get('company')
        location = request.form.get('location')
        description = request.form.get('description')
        requirements = request.form.get('requirements')
        salary_range = request.form.get('salary_range')
        job_type = request.form.get('job_type')
        
        new_job = Job(
            title=title,
            company=company,
            location=location,
            description=description,
            requirements=requirements,
            salary_range=salary_range,
            job_type=job_type,
            posted_by=current_user.id
        )
        
        db.session.add(new_job)
        db.session.commit()
        
        flash('Job posted successfully')
        return redirect(url_for('jobs'))
    
    return render_template('post_job.html')

@app.route('/messages')
@login_required
def messages():
    # Get all connections for messaging
    connections = current_user.get_connections()
    
    # Get recent messages
    received_messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    # Combine and sort by most recent
    all_messages = sorted(received_messages + sent_messages, key=lambda x: x.created_at, reverse=True)
    
    # Group by conversation partner
    conversations = {}
    for message in all_messages:
        partner_id = message.sender_id if message.recipient_id == current_user.id else message.recipient_id
        if partner_id not in conversations:
            partner = User.query.get(partner_id)
            conversations[partner_id] = {
                'partner': partner,
                'latest_message': message
            }
    
    return render_template('messages.html', conversations=conversations.values(), connections=connections)

@app.route('/conversation/<int:user_id>', methods=['GET', 'POST'])
@login_required
def conversation(user_id):
    partner = User.query.get_or_404(user_id)
    
    # Make sure users are connected
    if not current_user.is_connected(partner) and partner.id != current_user.id:
        flash('You can only message connections')
        return redirect(url_for('messages'))
    
    if request.method == 'POST':
        content = request.form.get('content')
        
        if content:
            new_message = Message(
                sender_id=current_user.id,
                recipient_id=partner.id,
                content=content
            )
            db.session.add(new_message)
            db.session.commit()
    
    # Get conversation messages
    sent = Message.query.filter_by(sender_id=current_user.id, recipient_id=partner.id).all()
    received = Message.query.filter_by(sender_id=partner.id, recipient_id=current_user.id).all()
    
    # Mark received messages as read
    for message in received:
        if not message.is_read:
            message.is_read = True
    
    db.session.commit()
    
    # Combine and sort by time
    messages = sorted(sent + received, key=lambda x: x.created_at)
    
    return render_template('conversation.html', partner=partner, messages=messages)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    
    if not query:
        return render_template('search_results.html', query='', users=[], jobs=[])
    
    # Search users
    users = User.query.filter(
        db.or_(
            User.first_name.ilike(f'%{query}%'),
            User.last_name.ilike(f'%{query}%'),
            User.headline.ilike(f'%{query}%')
        )
    ).all()
    
    # Search jobs
    jobs = Job.query.filter(
        db.or_(
            Job.title.ilike(f'%{query}%'),
            Job.company.ilike(f'%{query}%'),
            Job.description.ilike(f'%{query}%')
        )
    ).all()
    
    return render_template('search_results.html', query=query, users=users, jobs=jobs)

@app.route('/add_experience', methods=['GET', 'POST'])
@login_required
def add_experience():
    if request.method == 'POST':
        title = request.form.get('title')
        company = request.form.get('company')
        location = request.form.get('location')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        is_current = 'is_current' in request.form
        description = request.form.get('description')
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str and not is_current else None
        
        experience = Experience(
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=description,
            user_id=current_user.id
        )
        
        db.session.add(experience)
        db.session.commit()
        
        flash('Experience added successfully')
        return redirect(url_for('profile', user_id=current_user.id))
    
    return render_template('add_experience.html')

@app.route('/add_education', methods=['GET', 'POST'])
@login_required
def add_education():
    if request.method == 'POST':
        school = request.form.get('school')
        degree = request.form.get('degree')
        field_of_study = request.form.get('field_of_study')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        is_current = 'is_current' in request.form
        description = request.form.get('description')
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str and not is_current else None
        
        education = Education(
            school=school,
            degree=degree,
            field_of_study=field_of_study,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=description,
            user_id=current_user.id
        )
        
        db.session.add(education)
        db.session.commit()
        
        flash('Education added successfully')
        return redirect(url_for('profile', user_id=current_user.id))
    
    return render_template('add_education.html')

@app.route('/add_skill', methods=['POST'])
@login_required
def add_skill():
    skill_name = request.form.get('skill_name')
    
    if skill_name:
        # Check if skill already exists
        existing_skill = Skill.query.filter_by(name=skill_name, user_id=current_user.id).first()
        
        if not existing_skill:
            new_skill = Skill(name=skill_name, user_id=current_user.id)
            db.session.add(new_skill)
            db.session.commit()
            flash('Skill added successfully')
        else:
            flash('You already have this skill listed')
    
    return redirect(url_for('profile', user_id=current_user.id))

@app.route('/endorse_skill/<int:skill_id>', methods=['POST'])
@login_required
def endorse_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    
    # Make sure users are connected or it's not their own skill
    user = User.query.get(skill.user_id)
    if user.id != current_user.id and current_user.is_connected(user):
        skill.endorsements += 1
        db.session.commit()
        flash(f'You endorsed {user.first_name} for {skill.name}')
    
    return redirect(url_for('profile', user_id=skill.user_id))

@app.route('/notifications')
@login_required
def notifications():
    # This would be replaced with actual notifications
    # For demo purposes, we'll just show a placeholder
    return render_template('notifications.html')

# Main entry point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)