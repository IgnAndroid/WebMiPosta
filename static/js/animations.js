/**
 * Main initialization when DOM is fully loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    initBootstrapComponents();
    
    // Initialize form validations
    initFormValidations();
    
    // Initialize password toggles
    initPasswordToggles();
    
    // Initialize ripple effects
    initRippleEffects();
    
    // Initialize floating elements
    initFloatingElements();
    
    // Initialize scroll animations
    initScrollAnimations();
    
    // Add loaded class for CSS transitions
    window.addEventListener('load', () => {
        document.body.classList.add('page-loaded');
    });
});

/**
 * Initialize all Bootstrap components
 */
function initBootstrapComponents() {
    // Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(tooltipTriggerEl => {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Toasts
    const toastElList = [].slice.call(document.querySelectorAll('.toast:not(.manual-toast)'));
    toastElList.forEach(toastEl => {
        const toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 5000 });
        toast.show();
    });
}

    // Initialize Bootstrap toasts
    var toastElList = [].slice.call(document.querySelectorAll('.toast'));
    var toastList = toastElList.map(function(toastEl) {
      var toast = new bootstrap.Toast(toastEl, {autohide: true, delay: 5000});
      toast.show();
      return toast;
    });

/**
 * Initialize password visibility toggles
 */
function initPasswordToggles() {
    document.querySelectorAll('.toggle-password').forEach(button => {
        const input = button.closest('.input-group').querySelector('input');
        if (!input) return;
        
        button.addEventListener('click', function() {
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            const icon = this.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-eye');
                icon.classList.toggle('fa-eye-slash');
            }
        });
    });
}

/**
 * Initialize form validations and floating labels
 */
function initFormValidations() {
    // Handle all forms with validation
    document.querySelectorAll('form.needs-validation').forEach(form => {
        // Initialize floating labels
        initFloatingLabels(form);
        
        // Add form validation
        form.addEventListener('submit', handleFormSubmit);
    });
}

/**
 * Initialize floating labels for form inputs
 * @param {HTMLElement} form - The form element
 */
function initFloatingLabels(form) {
    const floatLabels = form.querySelectorAll('.form-control, .form-select');
    
    floatLabels.forEach(input => {
        const parent = input.parentElement;
        
        // Check initial value
        if (input.value) {
            parent.classList.add('focused');
        }
        
        // Add focus/blur events
        input.addEventListener('focus', () => {
            parent.classList.add('focused');
        });
        
        input.addEventListener('blur', () => {
            if (!input.value) {
                parent.classList.remove('focused');
            }
        });
    });
}

/**
 * Handle form submission with validation
 * @param {Event} event - The form submit event
 */
function handleFormSubmit(event) {
    const form = event.target;
    
    if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
        
        // Add shake animation to invalid fields
        const invalidFields = form.querySelectorAll(':invalid');
        invalidFields.forEach(field => {
            field.classList.add('is-invalid');
            field.addEventListener('animationend', () => {
                field.classList.remove('shake-animation');
            }, { once: true });
            field.classList.add('shake-animation');
        });
    } else {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            // Disable button and show loading state
            submitButton.disabled = true;
            const btnText = submitButton.querySelector('.btn-text');
            const spinner = submitButton.querySelector('.spinner-border');
            
            if (btnText) {
                const originalText = btnText.textContent;
                btnText.textContent = form.id === 'loginForm' ? 'Iniciando sesión...' : 'Creando cuenta...';
                
                // Store original text to restore if needed
                btnText.dataset.originalText = originalText;
            }
            
            if (spinner) {
                spinner.classList.remove('d-none');
            }
        }
    }
    
    form.classList.add('was-validated');
}

/**
 * Initialize ripple effects on buttons
 */
function initRippleEffects() {
    document.querySelectorAll('.btn:not(.no-ripple)').forEach(button => {
        button.addEventListener('click', function(e) {
            // Remove existing ripples
            const existingRipples = this.querySelectorAll('.ripple');
            existingRipples.forEach(ripple => ripple.remove());
            
            // Create new ripple
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            this.appendChild(ripple);
            
            // Remove ripple after animation
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

/**
 * Create floating background elements
 */
function initFloatingElements() {
    const container = document.querySelector('.login-page, .register-page');
    if (!container) return;
    
    // Remove existing floating elements
    container.querySelectorAll('.floating-element').forEach(el => el.remove());
    
    // Create new floating elements
    const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981'];
    
    for (let i = 0; i < 12; i++) {
        createFloatingElement(container, colors);
    }
}

/**
 * Create a single floating element
 * @param {HTMLElement} container - The container element
 * @param {string[]} colors - Array of color values
 */
function createFloatingElement(container, colors) {
    const element = document.createElement('div');
    element.className = 'floating-element';
    
    // Random properties
    const size = Math.random() * 120 + 30; // 30-150px
    const posX = Math.random() * 100;
    const posY = Math.random() * 100;
    const delay = Math.random() * 5;
    const duration = Math.random() * 15 + 10; // 10-25s
    const color = colors[Math.floor(Math.random() * colors.length)];
    const opacity = Math.random() * 0.3 + 0.1; // 0.1-0.4
    const blur = Math.random() * 15 + 5; // 5-20px
    const zIndex = Math.floor(Math.random() * 5);
    const borderRadius1 = Math.random() * 30 + 20; // 20-50%
    const borderRadius2 = 100 - borderRadius1; // Complementary value
    
    // Random rotation
    const rotation = Math.random() * 360;
    
    // Apply styles
    element.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        border-radius: ${borderRadius1}% ${borderRadius2}% ${borderRadius1}% ${borderRadius2}% / ${borderRadius2}% ${borderRadius1}% ${borderRadius2}% ${borderRadius1}%;
        left: ${posX}%;
        top: ${posY}%;
        opacity: ${opacity};
        filter: blur(${blur}px);
        z-index: ${zIndex};
        animation: float ${duration}s ease-in-out ${delay}s infinite alternate;
        pointer-events: none;
        transform: rotate(${rotation}deg);
        will-change: transform, opacity;
    `;
    
    container.prepend(element);
}

/**
 * Initialize scroll animations
 */
function initScrollAnimations() {
    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(initFloatingElements, 250);
    });
    
    // Initial animation check
    animateOnScroll();
    
    // Check on scroll
    window.addEventListener('scroll', animateOnScroll);
        </div>
        <button type="button" class="toast-close" aria-label="Cerrar">
          <i class="fas fa-times"></i>
        </button>
      `;
      
      // Add progress bar
      toast.prepend(progress);
      
      // Add close button functionality
      const closeBtn = toast.querySelector('.toast-close');
      closeBtn.addEventListener('click', () => {
        removeToast();
      });
      
      // Auto-remove after delay
      const autoRemove = setTimeout(removeToast, 5000);
      
      // Pause auto-remove on hover
      toast.addEventListener('mouseenter', () => {
        clearTimeout(autoRemove);
        progress.style.animationPlayState = 'paused';
      });
      
      toast.addEventListener('mouseleave', () => {
        progress.style.animationPlayState = 'running';
        setTimeout(removeToast, 2000);
      });
      
      // Add to container and show
      toastContainer.appendChild(toast);
      
      // Trigger reflow for animation
      toast.offsetHeight;
      
      return {
        element: toast,
        dismiss: removeToast
      };
    }
    
    function createToastContainer() {
      const container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
      return container;
    }
          title = 'Éxito';
          break;
        case 'error':
          icon = 'exclamation-circle';
          title = 'Error';
          break;
        case 'warning':
          icon = 'exclamation-triangle';
          title = 'Advertencia';
          break;
        default:
          icon = 'info-circle';
          title = 'Información';
      }

      toast.innerHTML = `
        <div class="toast-header">
          <strong class="me-auto">
            <i class="fas fa-${icon} text-${type} me-2"></i>${title}
          </strong>
          <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Cerrar"></button>
        </div>
        <div class="toast-body">
          ${message}
        </div>
      `;

      toastContainer.appendChild(toast);
      const bsToast = new bootstrap.Toast(toast, {autohide: true, delay: 5000});
      bsToast.show();

      // Remove toast after it's hidden
      toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
      });