from app import app, db, User, Project, BlogPost, Testimonial, Service, Statistic, TeamMember, ClientLogo, Certification

def create_admin():
    with app.app_context():
        # Check if admin user already exists
        if User.query.filter_by(username='admin').first() is None:
            admin_user = User(username='admin')
            # IMPORTANT: For a real application, use a more secure password and manage it properly.
            admin_user.set_password('MarogoAdmin2024!')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully. Username: admin, Password: MarogoAdmin2024!")
        else:
            print("Admin user already exists.")

def add_sample_data():
    with app.app_context():
        # Clear existing data to avoid duplicates on re-run
        Project.query.delete()
        BlogPost.query.delete()
        Testimonial.query.delete()
        ClientLogo.query.delete()
        Certification.query.delete()
        Statistic.query.delete()
        TeamMember.query.delete()
        Service.query.delete()
        
        db.session.commit()
        print("Cleared old sample data.")

        # Sample Projects
        p1 = Project(
            title="Lilongwe Commercial Building", 
            details="A multi-story commercial complex featuring modern architecture and sustainable design. This project was completed ahead of schedule and serves as a landmark in the city center.", 
            client="Phiri Investments", location="Lilongwe, Area 47", project_value="750M MWK", completion_date="December 2023", category="Building Construction", image_url="project1.webp"
        )
        db.session.add(p1)

        # Sample Blog Posts
        b1 = BlogPost(title="The Future of Sustainable Construction in Malawi", content="Exploring green building materials and energy-efficient designs is not just a trend; it's a necessity for a brighter future. Our latest projects incorporate solar power and rainwater harvesting...")
        db.session.add(b1)

        # Sample Testimonials
        t1 = Testimonial(author="John Phiri", position="CEO, Phiri Investments", quote="Marogo Civils delivered our project on time and exceeded our quality expectations. Their professionalism is unmatched in Malawi.")
        db.session.add(t1)
        
        # Sample Client Logos
        cl1 = ClientLogo(name="Malawi Revenue Authority", image_url="mra-logo.webp", website_url="https://www.mra.mw", order_num=1)
        cl2 = ClientLogo(name="ESCOM", image_url="escom-logo.webp", website_url="https://www.escom.mw", order_num=2)
        cl3 = ClientLogo(name="National Bank of Malawi", image_url="nbm-logo.webp", website_url="https://www.natbank.co.mw", order_num=3)
        db.session.add_all([cl1, cl2, cl3])
        
        # Sample Certifications
        c1 = Certification(name="500 Million Kwacha Category", issuing_body="National Construction Industry Council (NCIC)", icon_class="fas fa-award", order_num=1)
        c2 = Certification(name="Tax Compliant Certified", issuing_body="Malawi Revenue Authority (MRA)", icon_class="fas fa-check-circle", order_num=2)
        c3 = Certification(name="Certified in Advanced Site Safety", issuing_body="Malawi Institute of Engineers", icon_class="fas fa-user-shield", order_num=3)
        db.session.add_all([c1, c2, c3])
        
        db.session.commit()
        print("Sample data added successfully.")


if __name__ == '__main__':
    with app.app_context():
        # This creates the database file and all the tables
        db.create_all()
        print("Database tables created.")
    
    create_admin()
    # add_sample_data() # Uncomment this line if you want to populate your database with sample content.