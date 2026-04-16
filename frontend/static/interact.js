function getTimeAgo(timestamp) {
    if (!timestamp) return null;
    const now = new Date(new Date(). toISOString());
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffMin = Math.floor(diffMs / 60000);
    const diffHr = Math.floor(diffMin / 60);

    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin} min ago`;
    if (diffHr < 24) return `${diffHr}h ${diffMin % 60}m ago`;
    return `${Math.floor(diffHr / 24)}d ago`;
}

function getUrgencyColor(timestamp) {
    if (!timestamp) return '#6b7280';
    const diffMin = Math.floor((new Date() - new Date(timestamp)) / 60000);
    if (diffMin < 10) return '#e82a3d';
    if (diffMin < 30) return '#f97316';
    return '#6b7280';
}

function buildPopupMessage(signal) {
    const timeAgo = getTimeAgo(signal.timestamp);
    const urgencyColor = getUrgencyColor(signal.timestamp);

    return `
    <div style="font-family:'DM Sans',Arial,sans-serif;min-width:280px;max-width:320px;border-radius:16px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#e82a3d,#c41f30);padding:14px 16px;display:flex;align-items:center;gap:10px;">
            <div style="width:36px;height:36px;background:rgba(255,255,255,0.2);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.1rem;">🚨</div>
            <div style="flex:1;">
                <div style="color:white;font-weight:700;font-size:1rem;">Emergency Signal</div>
                <div style="color:rgba(255,255,255,0.75);font-size:0.78rem;">Active • Requires immediate attention</div>
            </div>
            ${timeAgo ? `
            <div style="background:rgba(255,255,255,0.15);border-radius:20px;padding:3px 10px;text-align:center;flex-shrink:0;">
                <div style="color:white;font-size:0.7rem;font-weight:700;">⏱️ ${timeAgo}</div>
            </div>` : ''}
        </div>
        <div style="padding:14px 16px;background:white;">
            <div style="display:flex;align-items:center;gap:10px;padding-bottom:12px;border-bottom:1px solid #f0f0f0;margin-bottom:12px;">
                <div style="width:40px;height:40px;background:linear-gradient(135deg,#e82a3d,#ff6b7a);border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:1.1rem;flex-shrink:0;">${(signal.user_name || 'U')[0].toUpperCase()}</div>
                <div>
                    <div style="font-weight:700;color:#1a1a2e;font-size:0.97rem;">${signal.user_name || 'Unknown'}</div>
                    <div style="display:flex;gap:6px;margin-top:2px;flex-wrap:wrap;">
                        ${signal.phone ? `<a href="tel:${signal.phone}" style="font-size:0.78rem;color:#e82a3d;text-decoration:none;background:#ffeaec;padding:2px 8px;border-radius:20px;">📞 ${signal.phone}</a>` : ''}
                        ${signal.email ? `<a href="mailto:${signal.email}" style="font-size:0.78rem;color:#e82a3d;text-decoration:none;background:#ffeaec;padding:2px 8px;border-radius:20px;">✉️ Email</a>` : ''}
                    </div>
                </div>
            </div>

            ${timeAgo ? `
            <div style="margin-bottom:10px;background:#f8f9fa;border-radius:10px;padding:8px 12px;display:flex;align-items:center;gap:8px;">
                <span style="font-size:1rem;">⏱️</span>
                <div>
                    <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.5px;color:#6b7280;">Active for</div>
                    <div style="font-size:0.9rem;font-weight:700;color:${urgencyColor};">${timeAgo}</div>
                </div>
            </div>` : ''}

            ${signal.causes ? `<div style="margin-bottom:8px;"><div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.5px;color:#6b7280;margin-bottom:3px;">Cause</div><div style="font-size:0.88rem;color:#e82a3d;font-weight:600;background:#ffeaec;padding:4px 10px;border-radius:8px;display:inline-block;">${signal.causes}</div></div>` : ''}
            ${signal.user_health ? `<div style="margin-bottom:8px;"><div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.5px;color:#6b7280;margin-bottom:3px;">Health Conditions</div><div style="font-size:0.88rem;color:#1a1a2e;">${signal.user_health}</div></div>` : ''}
            ${signal.details ? `<div style="margin-bottom:8px;"><div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.5px;color:#6b7280;margin-bottom:3px;">Details</div><div style="font-size:0.88rem;color:#1a1a2e;">${signal.details}</div></div>` : ''}
            ${signal.user_notes ? `<div style="margin-bottom:8px;"><div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.5px;color:#6b7280;margin-bottom:3px;">Notes</div><div style="font-size:0.88rem;color:#1a1a2e;">${signal.user_notes}</div></div>` : ''}

            <a href="https://maps.google.com/?q=${signal.lat},${signal.lng}" target="_blank" rel="noopener noreferrer" style="display:block;margin-top:12px;text-align:center;background:#1a1a2e;color:white;padding:8px;border-radius:10px;text-decoration:none;font-size:0.85rem;font-weight:600;">🗺️ View on Google Maps</a>
        </div>
    </div>`;
}

window.refreshMarkers = function () {
    if (!window.map) return;
    window.map.eachLayer((layer) => {
        if (layer instanceof L.CircleMarker) window.map.removeLayer(layer);
    });
    fetch('/api/signals?t=' + new Date().getTime())
        .then(res => res.json())
        .then(signals => {
            signals.forEach(signal => {
                if (signal.lat && signal.lng) {
                    const marker = L.circleMarker([signal.lat, signal.lng], {
                        radius: 12, fillColor: "#e82a3d", color: "white", weight: 2.5, fillOpacity: 0.9
                    }).addTo(window.map);
                    marker.bindPopup(buildPopupMessage(signal), { maxWidth: 340, className: 'custom-popup' });
                }
            });
        })
        .catch(err => console.error("Error loading map signals:", err));
};

window.updateStatsUI = function (stats) {
    if (!stats) return;
    if (document.getElementById('stat-total')) document.getElementById('stat-total').innerText = stats.total_signals;
    if (document.getElementById('stat-active')) document.getElementById('stat-active').innerText = stats.active_signals;
    if (document.getElementById('stat-resolved')) document.getElementById('stat-resolved').innerText = stats.resolved;
};

window.toggleEmergency = function () {
    const btn = document.getElementById('main-action-btn');
    const isCurrentlyActive = btn.getAttribute('data-active') === 'true';
    if (!isCurrentlyActive) {
        new bootstrap.Modal(document.getElementById('emergencyDetailsModal')).show();
    } else {
        new bootstrap.Modal(document.getElementById('resolveConfirmModal')).show();
    }
};

function showSpinner(status) {
    document.getElementById('emergency-form-view').style.display = 'none';
    document.getElementById('emergency-loading-view').style.display = 'block';
    document.getElementById('spinner-status').textContent = status || 'Locating your GPS position...';
}

function hideSpinner() {
    document.getElementById('emergency-form-view').style.display = 'block';
    document.getElementById('emergency-loading-view').style.display = 'none';
}

document.addEventListener("DOMContentLoaded", () => {
    window.refreshMarkers();

    const chips = document.querySelectorAll('.emergency-chip');
    const submitBtn = document.getElementById('confirm-emergency-btn');
    const detailsInput = document.getElementById('emergency-details-input');
    const mainBtn = document.getElementById('main-action-btn');
    const confirmResolveBtn = document.getElementById('confirm-resolve-btn');

    chips.forEach(chip => {
        chip.addEventListener('click', function () {
            this.classList.toggle('active');
            if (submitBtn) {
                submitBtn.disabled = document.querySelectorAll('.emergency-chip.active').length === 0;
            }
        });
    });

    const emergencyModal = document.getElementById('emergencyDetailsModal');
    if (emergencyModal) {
        emergencyModal.addEventListener('hidden.bs.modal', () => {
            hideSpinner();
            chips.forEach(c => c.classList.remove('active'));
            if (detailsInput) detailsInput.value = "";
            if (submitBtn) submitBtn.disabled = true;
        });
    }

    if (submitBtn) {
        submitBtn.addEventListener('click', () => {
            const selectedTypes = Array.from(document.querySelectorAll('.emergency-chip.active'))
                .map(chip => chip.innerText).join(', ');
            const additionalDetails = detailsInput ? detailsInput.value : "";

            showSpinner('Locating your GPS position...');

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition((pos) => {
                    document.getElementById('spinner-status').textContent = 'Sending emergency signal...';
                    fetch('/api/signal', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            lat: pos.coords.latitude,
                            lng: pos.coords.longitude,
                            conditions: selectedTypes,
                            notes: additionalDetails
                        })
                    })
                    .then(res => res.json())
                    .then(data => {
                        const modalEl = document.getElementById('emergencyDetailsModal');
                        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                        modal.hide();
                        if (mainBtn) {
                            mainBtn.setAttribute('data-active', 'true');
                            mainBtn.classList.remove('btn-emergency');
                            mainBtn.classList.add('btn-resolved');
                            mainBtn.innerText = "✅ RESOLVE EMERGENCY";
                        }
                        if (data.stats) window.updateStatsUI(data.stats);
                        window.refreshMarkers();
                    })
                    .catch(err => {
                        console.error("Fetch error:", err);
                        hideSpinner();
                        alert("Network error. Please try again.");
                    });
                }, () => {
                    hideSpinner();
                    alert("Please enable GPS services to send an emergency signal.");
                }, { enableHighAccuracy: true });
            } else {
                hideSpinner();
                alert("Geolocation is not supported by your browser.");
            }
        });
    }

    if (confirmResolveBtn) {
        confirmResolveBtn.addEventListener('click', () => {
            const resolveModal = bootstrap.Modal.getInstance(document.getElementById('resolveConfirmModal'));
            if (resolveModal) resolveModal.hide();
            const btn = document.getElementById('main-action-btn');
            btn.disabled = true;
            btn.innerText = "PROCESSING...";
            fetch('/api/resolve', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    btn.setAttribute('data-active', 'false');
                    btn.classList.remove('btn-resolved');
                    btn.classList.add('btn-emergency');
                    btn.innerText = "⚠️ EMERGENCY ⚠️";
                    btn.disabled = false;
                    if (data.stats) window.updateStatsUI(data.stats);
                    window.refreshMarkers();
                })
                .catch(err => {
                    console.error("Error resolving:", err);
                    btn.disabled = false;
                    btn.innerText = "✅ RESOLVE EMERGENCY";
                });
        });
    }

    const profileTags = document.querySelectorAll('.condition-tag');
    const hiddenInput = document.getElementById('selected-conditions-input');
    profileTags.forEach(tag => {
        tag.addEventListener('click', function () {
            this.classList.toggle('active');
            if (hiddenInput) {
                const activeTags = Array.from(document.querySelectorAll('.condition-tag.active')).map(t => t.innerText);
                hiddenInput.value = activeTags.join(', ');
            }
        });
    });
});