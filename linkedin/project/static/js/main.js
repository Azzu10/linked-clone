// LinkedIn Clone JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize post creation form
    initPostForm();
    
    // Initialize like functionality
    initLikeButtons();
    
    // Initialize comment forms
    initCommentForms();
    
    // Initialize search functionality
    initSearch();
    
    // Initialize profile picture upload preview
    initProfilePictureUpload();
    
    // Initialize date input handling for experience and education forms
    initDateInputs();
    
    // Initialize message sending
    initMessageSending();
    
    // Initialize notifications
    initNotifications();
    
    // Initialize mobile menu
    initMobileMenu();
});

// Tooltip initialization
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            const tooltipEl = document.createElement('div');
            tooltipEl.className = 'tooltip';
            tooltipEl.textContent = tooltipText;
            
            document.body.appendChild(tooltipEl);
            
            const rect = this.getBoundingClientRect();
            tooltipEl.style.top = `${rect.top - tooltipEl.offsetHeight - 5}px`;
            tooltipEl.style.left = `${rect.left + (rect.width / 2) - (tooltipEl.offsetWidth / 2)}px`;
            tooltipEl.style.opacity = '1';
        });
        
        tooltip.addEventListener('mouseleave', function() {
            const tooltipEl = document.querySelector('.tooltip');
            if (tooltipEl) {
                tooltipEl.remove();
            }
        });
    });
}

// Post form initialization
function initPostForm() {
    const postForm = document.getElementById('post-form');
    const postTextarea = document.getElementById('post-content');
    const postImageInput = document.getElementById('post-image');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeImageBtn = document.getElementById('remove-image');
    
    if (postForm) {
        // Handle textarea auto resize
        if (postTextarea) {
            postTextarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
        }
        
        // Handle image preview
        if (postImageInput) {
            postImageInput.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        imagePreview.src = e.target.result;
                        imagePreviewContainer.classList.remove('hidden');
                    };
                    
                    reader.readAsDataURL(this.files[0]);
                }
            });
        }
        
        // Remove image preview
        if (removeImageBtn) {
            removeImageBtn.addEventListener('click', function() {
                imagePreviewContainer.classList.add('hidden');
                imagePreview.src = '';
                postImageInput.value = '';
            });
        }
        
        // Handle form submission
        postForm.addEventListener('submit', function(e) {
            const content = postTextarea.value.trim();
            
            if (!content) {
                e.preventDefault();
                showToast('Please enter some content for your post', 'error');
            }
        });
    }
}

// Like button functionality
function initLikeButtons() {
    const likeButtons = document.querySelectorAll('.like-button');
    
    likeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const postId = this.getAttribute('data-post-id');
            const likeCountElement = document.querySelector(`.likes-count[data-post-id="${postId}"]`);
            
            fetch(`/like_post/${postId}`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.action === 'liked') {
                    this.classList.add('liked');
                    this.querySelector('i').classList.replace('far', 'fas');
                } else {
                    this.classList.remove('liked');
                    this.querySelector('i').classList.replace('fas', 'far');
                }
                
                if (likeCountElement) {
                    likeCountElement.textContent = data.likes_count + (data.likes_count === 1 ? ' like' : ' likes');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Something went wrong. Please try again.', 'error');
            });
        });
    });
}

// Comment form functionality
function initCommentForms() {
    const commentForms = document.querySelectorAll('.comment-form');
    
    commentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const postId = this.getAttribute('data-post-id');
            const commentInput = this.querySelector('.comment-input');
            const commentsContainer = document.querySelector(`.comments-container[data-post-id="${postId}"]`);
            
            if (!commentInput.value.trim()) {
                showToast('Please enter a comment', 'error');
                return;
            }
            
            const formData = new FormData(this);
            
            fetch(`/comment_post/${postId}`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Create new comment element
                    const newComment = document.createElement('div');
                    newComment.className = 'comment animate-fade-in';
                    newComment.innerHTML = `
                        <div class="comment-avatar">
                            <img src="/static/uploads/${currentUserAvatar || 'default_profile.jpg'}" alt="${currentUserName}" class="avatar avatar-sm">
                        </div>
                        <div class="comment-content">
                            <div class="comment-header">
                                <span class="comment-user">${data.author}</span>
                                <span class="comment-time">${data.created_at}</span>
                            </div>
                            <div class="comment-text">${data.content}</div>
                        </div>
                    `;
                    
                    commentsContainer.appendChild(newComment);
                    commentInput.value = '';
                    
                    // Update comment count
                    const commentCountElement = document.querySelector(`.comments-count[data-post-id="${postId}"]`);
                    if (commentCountElement) {
                        const currentCount = parseInt(commentCountElement.getAttribute('data-count') || 0);
                        const newCount = currentCount + 1;
                        commentCountElement.textContent = newCount + (newCount === 1 ? ' comment' : ' comments');
                        commentCountElement.setAttribute('data-count', newCount);
                    }
                    
                    showToast('Comment added successfully', 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Something went wrong. Please try again.', 'error');
            });
        });
    });
}

// Search functionality
function initSearch() {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    
    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', function(e) {
            if (!searchInput.value.trim()) {
                e.preventDefault();
                showToast('Please enter a search term', 'warning');
            }
        });
    }
}

// Profile picture upload preview
function initProfilePictureUpload() {
    const profilePictureInput = document.getElementById('profile-picture-input');
    const profilePicturePreview = document.getElementById('profile-picture-preview');
    const backgroundImageInput = document.getElementById('background-image-input');
    const backgroundImagePreview = document.getElementById('background-image-preview');
    
    if (profilePictureInput && profilePicturePreview) {
        profilePictureInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    profilePicturePreview.src = e.target.result;
                };
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
    
    if (backgroundImageInput && backgroundImagePreview) {
        backgroundImageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    backgroundImagePreview.src = e.target.result;
                };
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
}

// Date input handling for experience and education forms
function initDateInputs() {
    const isCurrentCheckboxes = document.querySelectorAll('.is-current-checkbox');
    
    isCurrentCheckboxes.forEach(checkbox => {
        const endDateInput = document.querySelector(`#${checkbox.getAttribute('data-controls')}`);
        
        if (endDateInput) {
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    endDateInput.disabled = true;
                    endDateInput.value = '';
                } else {
                    endDateInput.disabled = false;
                }
            });
            
            // Initialize on page load
            if (checkbox.checked) {
                endDateInput.disabled = true;
                endDateInput.value = '';
            }
        }
    });
}

// Message sending functionality
function initMessageSending() {
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('messages-container');
    
    if (messageForm && messageInput && messagesContainer) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!messageInput.value.trim()) {
                showToast('Please enter a message', 'error');
                return;
            }
            
            const formData = new FormData(this);
            const partnerId = this.getAttribute('data-partner-id');
            
            fetch(`/conversation/${partnerId}`, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    // Create new message element
                    const newMessage = document.createElement('div');
                    newMessage.className = 'message-bubble message-outgoing animate-slide-in';
                    newMessage.textContent = messageInput.value;
                    
                    messagesContainer.appendChild(newMessage);
                    messageInput.value = '';
                    
                    // Scroll to bottom
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    
                    return response.text();
                } else {
                    throw new Error('Network response was not ok');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Something went wrong. Please try again.', 'error');
            });
        });
        
        // Scroll to bottom on page load
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Notification functionality
function initNotifications() {
    // For demo purposes, we'll just show a notification after 5 seconds
    setTimeout(() => {
        showToast('Welcome to LinkedIn Clone!', 'info');
    }, 5000);
}

// Mobile menu functionality
function initMobileMenu() {
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
}

// Toast notification helper
function showToast(message, type = 'info') {
    // Remove any existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());
    
    // Create new toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const toastContent = `
        <div class="toast-header">
            <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <button class="toast-close">&times;</button>
        </div>
        <div class="toast-body">${message}</div>
    `;
    
    toast.innerHTML = toastContent;
    document.body.appendChild(toast);
    
    // Add close functionality
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', function() {
        toast.remove();
    });
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 5000);
}

// Helper function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString(undefined, options);
}

// Helper function to format times
function formatTime(dateString) {
    const date = new Date(dateString);
    const options = { hour: 'numeric', minute: 'numeric' };
    return date.toLocaleTimeString(undefined, options);
}