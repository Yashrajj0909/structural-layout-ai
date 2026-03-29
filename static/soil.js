
document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const detectLocationBtn = document.getElementById('detect-location');
    const exportPdfBtn = document.getElementById('export-pdf-btn');
    const langEnBtn = document.getElementById('lang-en');
    const langMrBtn = document.getElementById('lang-mr');

    const translations = {
        en: {
            h1: "Soil & FSI Analysis",
            city: "City / Area Name",
            pincode: "Pincode",
            analyze: "Analyze",
        },
        mr: {
            h1: "माती आणि एफएसआय विश्लेषण",
            city: "शहर / परिसराचे नाव",
            pincode: "पिनकोड",
            analyze: "विश्लेषण करा",
        }
    };

    langEnBtn.addEventListener('click', () => setLanguage('en'));
    langMrBtn.addEventListener('click', () => setLanguage('mr'));

    function setLanguage(lang) {
        document.querySelector('h1').textContent = translations[lang].h1;
        document.getElementById('city').placeholder = translations[lang].city;
        document.getElementById('pincode').placeholder = translations[lang].pincode;
        document.getElementById('analyze-btn').textContent = translations[lang].analyze;
        langEnBtn.classList.toggle('active', lang === 'en');
        langMrBtn.classList.toggle('active', lang === 'mr');
    }

    analyzeBtn.addEventListener('click', async () => {
        if (!validateForm()) return;

        analyzeBtn.innerHTML = 'Analyzing...';
        analyzeBtn.disabled = true;

        const requestData = {
            city: document.getElementById('city').value,
            pincode: document.getElementById('pincode').value,
            lat: parseFloat(document.getElementById('lat').value) || null,
            lon: parseFloat(document.getElementById('lon').value) || null,
            plot_area: parseFloat(document.getElementById('plot-area').value),
            locality_type: document.getElementById('locality-type').value,
        };

        try {
            const response = await fetch('/api/v1/soil/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail?.[0]?.msg || err.detail || 'Analysis failed');
            }

            const results = await response.json();
            displayResults(results);
            showToast('Analysis complete!', 'success');
        } catch (error) {
            console.error('Error during analysis:', error);
            showToast('Error: ' + error.message, 'error');
        } finally {
            analyzeBtn.innerHTML = 'Analyze';
            analyzeBtn.disabled = false;
        }
    });

    function validateForm() {
        const plotArea = document.getElementById('plot-area').value;
        if (plotArea <= 0) {
            showToast('Plot area must be greater than 0.', 'error');
            return false;
        }
        const pincode = document.getElementById('pincode').value;
        if (pincode.length !== 6 || !/^[0-9]+$/.test(pincode)) {
            showToast('Pincode must be 6 digits.', 'error');
            return false;
        }
        return true;
    }

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    detectLocationBtn.addEventListener('click', () => {
        if (navigator.geolocation) {
            detectLocationBtn.innerHTML = 'Detecting...';
            detectLocationBtn.disabled = true;
            navigator.geolocation.getCurrentPosition(async (position) => {
                document.getElementById('lat').value = position.coords.latitude.toFixed(4);
                document.getElementById('lon').value = position.coords.longitude.toFixed(4);
                // Mock reverse geocoding
                document.getElementById('city').value = "Pune";
                document.getElementById('pincode').value = "411001";
                detectLocationBtn.innerHTML = 'Detect Location';
                detectLocationBtn.disabled = false;
            }, (error) => {
                alert('Error detecting location: ' + error.message);
                detectLocationBtn.innerHTML = 'Detect Location';
                detectLocationBtn.disabled = false;
            });
        } else {
            alert('Geolocation is not supported by this browser.');
        }
    });

    exportPdfBtn.addEventListener('click', () => {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        doc.text("Soil & FSI Analysis Report", 20, 20);
        // This is a simplified example. A real implementation would be more complex.
        doc.text("Location: " + document.getElementById('city').value, 20, 30);
        doc.save("soil-analysis-report.pdf");
    });

    function displayResults(results) {
        if (!results || !results.soil_analysis || !results.fsi_analysis) {
            console.error('Invalid results structure:', results);
            showToast('Invalid analysis results received', 'error');
            return;
        }

        const soilSection = document.getElementById('soil-analysis');
        soilSection.innerHTML = `<h3>Soil Analysis</h3>
            <p>Bearing Capacity: ${results.soil_analysis.bearing_capacity}</p>
            <p>Water Retention: ${results.soil_analysis.water_retention}</p>
            <p>Suitability Score: ${results.soil_analysis.suitability_score}</p>
            <p>Health: ${results.soil_analysis.health}</p>`;

        const fsiSection = document.getElementById('fsi-analysis');
        fsiSection.innerHTML = `<h3>FSI Calculation</h3>
            <p>Allowed FSI: ${results.fsi_analysis.allowed_fsi}</p>
            <p>Max Construction Area: ${results.fsi_analysis.max_construction_area} sq. m</p>`;

        const suitabilitySection = document.getElementById('construction-suitability');
        suitabilitySection.innerHTML = `<h3>Construction Suitability</h3>
            <p>Status: ${results.construction_suitability.status}</p>
            <ul>${results.construction_suitability.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>`;

        const insightsSection = document.getElementById('ai-insights');
        insightsSection.innerHTML = `<h3>AI Insights</h3>
            <ul>${results.ai_insights.map(i => `<li>${i}</li>`).join('')}</ul>`;

        createCharts(results);
    }

    function createCharts(results) {
        const soilCtx = document.getElementById('soil-chart').getContext('2d');
        if (window.soilChart) window.soilChart.destroy();
        window.soilChart = new Chart(soilCtx, {
            type: 'bar',
            data: {
                labels: ['Bearing Capacity', 'Water Retention', 'Suitability Score'],
                datasets: [{
                    label: 'Soil Metrics',
                    data: [
                        parseFloat(results.soil_analysis.bearing_capacity),
                        parseFloat(results.soil_analysis.water_retention),
                        results.soil_analysis.suitability_score
                    ],
                    backgroundColor: '#B5651D'
                }]
            }
        });

        const fsiCtx = document.getElementById('fsi-chart').getContext('2d');
        if (window.fsiChart) window.fsiChart.destroy();
        window.fsiChart = new Chart(fsiCtx, {
            type: 'doughnut',
            data: {
                labels: ['Max Construction Area', 'Plot Area'],
                datasets: [{
                    data: [results.fsi_analysis.max_construction_area, document.getElementById('plot-area').value],
                    backgroundColor: ['#B5651D', '#3D5A6C']
                }]
            }
        });
    }
});
