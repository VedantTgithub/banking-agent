document.getElementById('underwrite-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const formView = document.getElementById('form-view');
    const loadingOverlay = document.getElementById('loading-overlay');
    const resultsView = document.getElementById('results-view');
    const submitBtn = document.getElementById('submit-btn');

    // Show loading
    formView.style.display = 'none';
    loadingOverlay.style.display = 'block';
    submitBtn.disabled = true;

    try {
        const response = await fetch('/api/underwrite', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to process application');
        }

        const data = await response.json();
        displayResults(data);
    } catch (err) {
        alert('Error: ' + err.message);
        formView.style.display = 'block';
        loadingOverlay.style.display = 'none';
        submitBtn.disabled = false;
    }
});

function displayResults(state) {
    document.getElementById('loading-overlay').style.display = 'none';
    document.getElementById('results-view').style.display = 'block';

    // Header info
    document.getElementById('result-app-id').textContent = state.application_id;
    document.getElementById('result-applicant').textContent = state.applicant_name;
    
    const verdictBadge = document.getElementById('verdict-badge');
    verdictBadge.textContent = state.decision || 'SHORT-CIRCUITED';
    verdictBadge.className = `verdict-badge verdict-${state.decision || 'ESCALATED'}`;

    // Tab 1: Doc Check
    document.getElementById('ext-name').textContent = state.extracted_name || 'N/A';
    document.getElementById('ext-income').textContent = `₹${(state.extracted_income || 0).toLocaleString()}`;
    document.getElementById('doc-status').textContent = state.doc_verified ? 'VERIFIED' : 'FAILED';
    
    renderFlags('doc-flags', state.doc_flags);

    // Tab 2: Credit
    document.getElementById('bureau-score').textContent = state.bureau_score || '0';
    document.getElementById('dti-ratio').textContent = `${(state.dti_ratio || 0).toFixed(1)}%`;
    document.getElementById('foir').textContent = `${(state.foir || 0).toFixed(1)}%`;
    renderFlags('credit-flags', state.credit_flags);

    // Tab 3: Risk
    document.getElementById('risk-tier').textContent = (state.risk_tier || 'N/A').toUpperCase();
    document.getElementById('ltv-ratio').textContent = `${(state.ltv_ratio || 0).toFixed(1)}%`;
    document.getElementById('collateral-score').textContent = (state.collateral_score || 0).toFixed(2);
    renderFlags('risk-flags', state.risk_flags);

    // Tab 4: Policy
    const policyStatus = document.getElementById('policy-status');
    policyStatus.innerHTML = state.compliance_passed ? 
        '<div style="color: #10b981; font-weight: 700;">✅ COMPLIANCE PASSED</div>' : 
        '<div style="color: #ef4444; font-weight: 700;">❌ POLICY VIOLATIONS DETECTED</div>';
    
    const violationsDiv = document.getElementById('policy-violations');
    violationsDiv.innerHTML = (state.violations || []).map(v => `
        <div style="padding: 0.75rem; background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; margin-bottom: 0.5rem;">
            ${v}
        </div>
    `).join('');

    document.getElementById('policy-rules').textContent = 'Rules Checked: ' + (state.applicable_rules || []).join(', ');

    // Tab 5: Verdict
    document.getElementById('decision-report').textContent = state.decision_report || 'No detailed report generated.';
    document.getElementById('rec-terms').textContent = JSON.stringify(state.recommended_terms || {}, null, 2);

    lucide.createIcons();
}

function renderFlags(containerId, flags) {
    const container = document.getElementById(containerId);
    container.innerHTML = (flags || []).map(f => `
        <div class="flag">
            <i data-lucide="alert-triangle" style="width: 16px; height: 16px;"></i>
            ${f}
        </div>
    `).join('');
}

function showTab(tabId) {
    // Hide all contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    // Remove active from all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    // Show target
    document.getElementById(tabId).classList.add('active');
    // Add active to button
    event.currentTarget.classList.add('active');
    
    lucide.createIcons();
}
