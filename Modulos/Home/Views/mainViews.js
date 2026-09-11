// Views/mainViews.js

const MainViews = {
    /**
     * Renderiza el esqueleto base comercial consumiendo el modelo de datos.
     * @param {Object} data - Matriz de textos estructurada de la Landing
     */
    obtenerLandingHTML: (data) => {
        const content = data;

        return `
            <header>
                <h1>${content.hero.title}</h1>
                <h2>${content.hero.tagline}</h2>
                <p>${content.hero.description}</p>
                <button id="heroCta">${content.hero.cta}</button>
            </header>
            
            <section id="problem">
                <h3>${content.problem.title}</h3>
                <ul>
                    ${content.problem.items.map(item => `<li>❌ ${item}</li>`).join('')}
                </ul>
            </section>
            
            <section id="features">
                ${content.features.map(f => `
                    <div class="feature-card">
                        <h4>${f.title}</h4>
                        <p>${f.desc}</p>
                    </div>
                `).join('')}
            </section>
            
            <section id="pricing">
                <h3>${content.pricing.title}</h3>
                <div class="price-card">
                    <h4>${content.pricing.type}</h4>
                    <div class="price-tag">${content.pricing.price}</div>
                    <p><em>${content.pricing.period}</em></p>
                    <ul>
                        ${content.pricing.benefits.map(b => `<li>✓ ${b}</li>`).join('')}
                    </ul>
                </div>
            </section>
        `;
    },

    obtenerBarraSuperiorHTML: (nombreAdmin) => {
        return `<span>🔥 Bienvenido, <strong>${nombreAdmin}</strong></span>`;
    }
};