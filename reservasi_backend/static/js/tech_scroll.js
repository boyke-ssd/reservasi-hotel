document.addEventListener('DOMContentLoaded', function() {
    // Get the technologies container
    const techContainer = document.querySelector('.technologies-container');
    
    // If found, convert it to a horizontal scrolling container
    if (techContainer) {
        // Remove grid classes and add flex with overflow
        techContainer.classList.remove('grid', 'grid-cols-1', 'sm:grid-cols-2', 'md:grid-cols-3', 'lg:grid-cols-4', 'gap-6');
        techContainer.classList.add('flex', 'overflow-x-auto', 'scrollbar-hide', 'py-4', 'space-x-6');
        
        // Make each tech item a fixed width
        const techItems = techContainer.querySelectorAll('.tech-item');
        techItems.forEach(item => {
            item.classList.remove('mb-6');
            item.classList.add('min-w-[250px]', 'flex-shrink-0');
        });
    }
});
