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
                <a href="launcher_api/Cenizas de Alejandría - Core 1.0.0.zip" download="Cenizas de Alejandría - Core 1.0.0.zip" id="heroCta" class="hero-btn" style="display: inline-block; padding: 10px 20px; background-color: #0288d1; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">${content.hero.cta}</a>
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