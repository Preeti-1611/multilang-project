// Global variables
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let currentTheme = 'light';

// DOM elements
const recordBtn = document.getElementById('recordBtn');
const micIcon = document.getElementById('micIcon');
const recordText = document.getElementById('recordText');
const statusDiv = document.getElementById('status');
const spinner = document.getElementById('spinner');
const historyBtn = document.getElementById('historyBtn');
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeSettings = document.getElementById('closeSettings');
const darkModeToggle = document.getElementById('darkModeToggle');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadTheme();
});

// Initialize application
function initializeApp() {
    // Check for browser support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Your browser does not support audio recording. Please use a modern browser.');
        recordBtn.disabled = true;
        recordBtn.style.opacity = '0.5';
    }
    
    // Initialize tooltips and animations
    initializeAnimations();
    
    // Start typing animation
    startTypingAnimation();
}

// Setup event listeners
function setupEventListeners() {
    // Recording functionality
    recordBtn.addEventListener('click', handleRecording);
    
    // Navigation
    historyBtn.addEventListener('click', toggleHistory);
    settingsBtn.addEventListener('click', openSettings);
    closeSettings.addEventListener('click', closeSettingsModal);
    
    // Theme toggle
    darkModeToggle.addEventListener('click', toggleTheme);
    
    // Modal backdrop click
    settingsModal.addEventListener('click', function(e) {
        if (e.target === settingsModal) {
            closeSettingsModal();
        }
    });
    

    
    // Clear history
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', clearHistory);
    }
    
    // Theme options
    document.querySelectorAll('.theme-option').forEach(option => {
        option.addEventListener('click', function() {
            const theme = this.dataset.theme;
            setTheme(theme);
        });
    });
}

// Handle recording functionality
async function handleRecording() {
    if (!isRecording) {
        await startRecording();
    } else {
        stopRecording();
    }
}

// Start recording
async function startRecording() {
    try {
        // Request microphone permission
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        // Initialize MediaRecorder
        mediaRecorder = new MediaRecorder(stream, { 
            mimeType: 'audio/webm;codecs=opus' 
        });
        
        // Setup recording handlers
        audioChunks = [];
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorder.onstop = handleRecordingComplete;
        
        // Start recording
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        updateRecordingUI(true);
        showStatus('Listening...', 'info');
        
        // Add recording animation
        recordBtn.classList.add('recording');
        
    } catch (error) {
        console.error('Error starting recording:', error);
        showError('Failed to start recording. Please check microphone permissions.');
    }
}

// Stop recording
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // Update UI
        updateRecordingUI(false);
        showStatus('Processing...', 'info');
        showSpinner(true);
        
        // Stop all tracks
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
}

// Handle recording completion
async function handleRecordingComplete() {
    try {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        
        // Check if audio has content
        if (audioBlob.size < 1000) {
            showError('No speech detected. Please try speaking louder or check your microphone.');
            showSpinner(false);
            return;
        }
        
        // Prepare form data
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('output_lang', document.getElementById('outputLang').value);
            formData.append('input_lang', document.getElementById('inputLang').value);

        // Send to server
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
            const data = await response.json();
        
        // Handle response
        if (data.error) {
            showError(data.error);
            } else {
            displayResults(data);
            showSuccess('Translation completed successfully!');
        }
        
    } catch (error) {
        console.error('Error processing recording:', error);
        showError('Failed to process recording. Please try again.');
    } finally {
        showSpinner(false);
    }
}

// Update recording UI
function updateRecordingUI(recording) {
    if (recording) {
        recordText.textContent = 'Stop Recording';
        micIcon.className = 'fas fa-stop';
        recordBtn.classList.add('recording');
    } else {
        recordText.textContent = 'Click to Start Recording';
        micIcon.className = 'fas fa-microphone';
        recordBtn.classList.remove('recording');
    }
}

// Display results
function displayResults(data) {
    const recognizedText = document.getElementById('recognizedText');
    const translatedText = document.getElementById('translatedText');
    const audioPlayer = document.getElementById('audioPlayer');
    
    // Animate text appearance
    animateText(recognizedText, `Recognized: ${data.recognized}`);
    
    const langName = document.getElementById('outputLang').selectedOptions[0].text;
    animateText(translatedText, `Translated (${langName}): ${data.translated}`);
    
    // Handle audio playback
    if (data.audio_file) {
        audioPlayer.src = `/audio/${data.audio_file}?t=${Date.now()}`;
        audioPlayer.style.display = 'block';
        
        // Auto-play if enabled
        const autoPlay = document.getElementById('autoPlayToggle');
        if (autoPlay && autoPlay.checked) {
            audioPlayer.play().catch(e => {});
        }
        
        showStatus('Audio ready for playback', 'success');
    } else {
        audioPlayer.style.display = 'none';
        showStatus('Translation completed', 'success');
    }
}

// Animate text appearance
function animateText(element, text) {
    element.style.opacity = '0';
    element.textContent = text;
    
    setTimeout(() => {
        element.style.transition = 'opacity 0.5s ease';
        element.style.opacity = '1';
    }, 100);
}



// Toggle history
function toggleHistory() {
    const historySection = document.getElementById('history-section');
    const isVisible = historySection.style.display !== 'none';
    
    if (!isVisible) {
        loadHistory();
    }
    
    historySection.style.display = isVisible ? 'none' : 'block';
    
    // Smooth scroll to history
    if (!isVisible) {
        historySection.scrollIntoView({ behavior: 'smooth' });
    }
}

// Load history
async function loadHistory() {
    try {
        const response = await fetch('/history');
        const history = await response.json();
        
        const historyList = document.getElementById('history-list');
        historyList.innerHTML = '';
        
        if (history.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h4>No translation history yet</h4>
                    <p>Your translation history will appear here</p>
                </div>
            `;
        } else {
            history.slice().reverse().forEach(item => {
                const historyItem = createHistoryItem(item);
                historyList.appendChild(historyItem);
            });
        }
    } catch (error) {
        console.error('Error loading history:', error);
        showError('Failed to load history.');
    }
}

// Create history item
function createHistoryItem(item) {
    const div = document.createElement('div');
    div.className = 'history-item';
    
    div.innerHTML = `
        <div class="history-content">
            <div class="history-text">
                <strong>Recognized:</strong>
                <p>${item.recognized}</p>
            </div>
            <div class="history-text">
                <strong>Translated:</strong>
                <p>${item.translated}</p>
            </div>
        </div>
        <div class="history-meta">
            <span>${new Date(item.timestamp).toLocaleString()}</span>
            <button class="delete-btn" onclick="deleteHistoryItem('${item.timestamp}')">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        ${item.audio_file ? `
            <div class="history-audio">
                <audio controls src="/audio/${item.audio_file}"></audio>
            </div>
        ` : ''}
    `;
    
    return div;
}

// Delete history item
async function deleteHistoryItem(timestamp) {
    try {
        const response = await fetch('/history/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ timestamp })
        });
        
        if (response.ok) {
            loadHistory(); // Reload history
            showSuccess('History item deleted');
        } else {
            throw new Error('Failed to delete history item');
        }
    } catch (error) {
        console.error('Error deleting history item:', error);
        showError('Failed to delete history item');
    }
}

// Clear history
async function clearHistory() {
    if (!confirm('Are you sure you want to clear all history?')) {
        return;
    }
    
    try {
        const response = await fetch('/history/clear', { method: 'POST' });
        
        if (response.ok) {
            loadHistory(); // Reload history
            showSuccess('History cleared successfully');
        } else {
            throw new Error('Failed to clear history');
        }
    } catch (error) {
        console.error('Error clearing history:', error);
        showError('Failed to clear history');
    }
}

// Settings functionality
function openSettings() {
    settingsModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeSettingsModal() {
    settingsModal.classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Theme functionality
function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

function setTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update theme toggle UI
    darkModeToggle.checked = theme === 'dark';
    
    // Update theme options
    document.querySelectorAll('.theme-option').forEach(option => {
        option.classList.remove('active');
        if (option.dataset.theme === theme) {
            option.classList.add('active');
        }
    });
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
}

// Utility functions
function showStatus(message, type = 'info') {
    statusDiv.textContent = message;
    statusDiv.className = `status-text status-${type}`;
}

function showSpinner(show) {
    spinner.style.display = show ? 'flex' : 'none';
}

function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast(message, 'error');
    console.error(message);
}

function showToast(message, type = 'info') {
    toastMessage.textContent = message;
    toast.className = `toast toast-${type}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Initialize animations
function initializeAnimations() {
    // Add intersection observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.translation-card, .history-section').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Typing animation for hero subtitle
function startTypingAnimation() {
    const subtitle = document.querySelector('.hero-subtitle');
    if (!subtitle) return;
    
    const fullText = subtitle.textContent;
    subtitle.textContent = '';
    subtitle.style.borderRight = '2px solid #6366f1';
    subtitle.style.overflow = 'visible';
    subtitle.style.whiteSpace = 'normal';
    
    let i = 0;
    const typeWriter = () => {
        if (i < fullText.length) {
            subtitle.textContent += fullText.charAt(i);
        i++;
            setTimeout(typeWriter, 30);
        } else {
            // Remove cursor after typing is complete
            setTimeout(() => {
                subtitle.style.borderRight = 'none';
            }, 1000);
      }
    };
    
    // Start typing after a short delay
    setTimeout(typeWriter, 500);
  }
  
// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to start/stop recording
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleRecording();
    }
    
    // Escape to close modal
    if (e.key === 'Escape') {
        closeSettingsModal();
    }
});

// Service Worker registration (for PWA capabilities)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                // Service worker registered successfully
            })
            .catch(registrationError => {
                // Service worker registration failed
        });
    });
}

// Export functions for global access
window.deleteHistoryItem = deleteHistoryItem;