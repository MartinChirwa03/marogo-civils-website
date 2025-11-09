document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for anchor links (if any)
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // --- NEW: Mobile Navigation Drawer Logic ---
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenuClose = document.querySelector('.mobile-menu-close');
    const mobileNavDrawer = document.querySelector('.mobile-nav-drawer');
    const navOverlay = document.querySelector('.nav-overlay');
    const body = document.body;

    function openMobileMenu() {
        body.classList.add('mobile-menu-is-open');
    }

    function closeMobileMenu() {
        body.classList.remove('mobile-menu-is-open');
    }

    if (mobileMenuToggle && mobileNavDrawer && mobileMenuClose && navOverlay) {
        mobileMenuToggle.addEventListener('click', openMobileMenu);
        mobileMenuClose.addEventListener('click', closeMobileMenu);
        navOverlay.addEventListener('click', closeMobileMenu);
    }

    // Header scroll effect logic
    const header = document.querySelector('.main-nav');
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }

    // AJAX Contact form logic
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formStatus = document.getElementById('form-status');
            const submitButton = contactForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            submitButton.disabled = true;
            submitButton.innerHTML = 'Sending...';
            formStatus.innerHTML = '';
            const formData = new FormData(contactForm);
            fetch('/contact', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    formStatus.innerHTML = `<p class="flash-success">${data.message}</p>`;
                    contactForm.reset();
                    submitButton.innerHTML = 'Sent!';
                } else {
                    formStatus.innerHTML = `<p class="flash-danger">An error occurred. Please try again.</p>`;
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalButtonText;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                formStatus.innerHTML = `<p class="flash-danger">A network error occurred. Please check your connection.</p>`;
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
            });
        });
    }

    // Project filtering logic
    const filterContainer = document.querySelector('#project-filters');
    const projectsContainer = document.querySelector('#projects-container');
    if (filterContainer && projectsContainer) {
        const projectItems = projectsContainer.querySelectorAll('.filterable-item');
        filterContainer.addEventListener('click', function(e) {
            if (e.target.classList.contains('filter-btn')) {
                filterContainer.querySelector('.active').classList.remove('active');
                e.target.classList.add('active');
                const filterValue = e.target.getAttribute('data-filter');
                projectItems.forEach(item => {
                    item.classList.add('hidden');
                    setTimeout(() => {
                        if (filterValue === 'all' || item.dataset.category === filterValue) {
                           item.parentElement.style.display = 'block';
                        } else {
                           item.parentElement.style.display = 'none';
                        }
                        setTimeout(() => {
                            if (filterValue === 'all' || item.dataset.category === filterValue) {
                                item.classList.remove('hidden');
                            }
                        }, 20);
                    }, 400);
                });
            }
        });
    }

    // Animation on Scroll Logic
    const animatedElements = document.querySelectorAll('.fade-in, .slide-up, .slide-in-left, .slide-in-right');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    animatedElements.forEach(element => observer.observe(element));

    // Stats Counter Logic (now dynamic from data-target)
    const statsSection = document.querySelector('.stats-section');
    if (statsSection) {
        const statNumbers = document.querySelectorAll('.stat-number');
        const startCounter = (el) => {
            const target = +el.dataset.target;
            let current = 0;
            const increment = target / 100; // Animate over roughly 100 steps
            const updateCounter = () => {
                if (current < target) {
                    current += increment;
                    el.textContent = Math.ceil(current);
                    requestAnimationFrame(updateCounter);
                } else {
                    el.textContent = target; // Ensure it ends on the exact number
                }
            };
            updateCounter();
        };

        const statsObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                statNumbers.forEach(startCounter);
                statsObserver.unobserve(statsSection); // Only run once
            }
        }, { threshold: 0.5 });
        statsObserver.observe(statsSection);
    }

    // Testimonials Carousel Logic
    const carouselWrapper = document.querySelector('.testimonial-carousel-wrapper');
    if (carouselWrapper) {
        const carousel = carouselWrapper.querySelector('.testimonial-carousel');
        const testimonials = carousel.querySelectorAll('.testimonial-item');
        const dotsContainer = carouselWrapper.querySelector('.testimonial-dots');

        if (testimonials.length > 1) {
            let currentIndex = 0;
            let intervalId;

            // Create dots
            testimonials.forEach((_, index) => {
                const dot = document.createElement('button');
                dot.classList.add('testimonial-dot');
                dot.dataset.index = index;
                if (index === 0) {
                    dot.classList.add('active');
                }
                dotsContainer.appendChild(dot);
            });

            const dots = dotsContainer.querySelectorAll('.testimonial-dot');

            const updateCarousel = (index) => {
                carousel.style.transform = `translateX(-${index * 100}%)`;
                dots.forEach(d => d.classList.remove('active'));
                dots[index].classList.add('active');
                currentIndex = index;
            };

            const nextTestimonial = () => {
                const nextIndex = (currentIndex + 1) % testimonials.length;
                updateCarousel(nextIndex);
            };

            const startCarousel = () => {
                intervalId = setInterval(nextTestimonial, 5000); // Change testimonial every 5 seconds
            };

            const stopCarousel = () => {
                clearInterval(intervalId);
            };

            dotsContainer.addEventListener('click', (e) => {
                if (e.target.matches('.testimonial-dot')) {
                    const index = parseInt(e.target.dataset.index, 10);
                    updateCarousel(index);
                }
            });

            carouselWrapper.addEventListener('mouseenter', stopCarousel);
            carouselWrapper.addEventListener('mouseleave', startCarousel);

            startCarousel(); // Initial start
        }
    }
});