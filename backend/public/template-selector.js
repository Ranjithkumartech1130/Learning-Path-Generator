// Global variable for selected template
let selectedTemplate = 'coral'; // Default template

// Template selection function
function selectTemplate(templateName) {
    selectedTemplate = templateName;

    // Update UI - remove active class from all
    document.querySelectorAll('.template-card').forEach(card => {
        card.classList.remove('active');
    });

    // Add active class to selected
    const selectedCard = document.querySelector(`[data-template="${templateName}"]`);
    if (selectedCard) {
        selectedCard.classList.add('active');
    }
}
