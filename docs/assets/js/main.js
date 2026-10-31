// n8n SaaS Factory — GitHub Pages JS

document.addEventListener('DOMContentLoaded', () => {
  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    });
  });

  // Intersection observer for fade-in animations
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.section, .feature-card, .arch-box').forEach(el => {
    observer.observe(el);
  });

  // Mobile nav toggle
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
    });
  }

  // Language switcher
  const currentPath = window.location.pathname;
  const langLinks = document.querySelectorAll('.lang-switch a');
  langLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href && currentPath.startsWith(href.replace(/\/$/, ''))) {
      link.classList.add('active');
    }
  });
});