document.addEventListener('DOMContentLoaded', () => {
    console.log("Portal de Empleo Dark Theme Cargado");

    // Ejemplo: interacción con las pestañas de navegación secundaria
    const navLinks = document.querySelectorAll('.secondary-nav ul li');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Prevenir comportamiento por defecto si es un enlace <a>
            // e.preventDefault(); (descomentar si los href="#" causan saltos)

            // Quitar 'active' de todas las pestañas
            navLinks.forEach(item => item.classList.remove('active'));
            // Añadir 'active' a la pestaña clickeada
            this.classList.add('active');

            // Aquí podrías cargar contenido diferente basado en la pestaña
            const tabName = this.querySelector('a').textContent;
            console.log(`Pestaña activa: ${tabName}`);
        });
    });

    // Ejemplo: botón CTA
    const ctaButton = document.querySelector('.cta-button');
    if (ctaButton) {
        ctaButton.addEventListener('click', () => {
            alert('Acción: Finalizar CV');
        });
    }
});