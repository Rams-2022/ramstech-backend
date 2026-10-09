"""Event handlers — wire the event bus into real-time tab behaviour."""
from fastapi import APIRouter

router = APIRouter()

EVENT_HANDLERS_HTML = r"""
<script>
(function(){
  // Wait for event bus + all modules to be ready
  function waitForBus(callback){
    var tries = 0;
    var t = setInterval(function(){
      tries++;
      if(typeof window.dpOn === 'function' && typeof window.dpEmit === 'function'){
        clearInterval(t);
        callback();
      } else if(tries > 60){
        clearInterval(t);
        console.warn('[handlers] Event bus never loaded');
      }
    }, 250);
  }

  waitForBus(function(){

    // ═══════════════════════════════════════════════════
    // A. KANBAN REACTS LIVE TO WORKFLOW EVENTS
    // ═══════════════════════════════════════════════════
    var kanbanEvents = [
      'job.created', 'job.assigned', 'job.started',
      'job.progress', 'job.completed', 'job.qc_passed',
      'invoice.created', 'job.cost_set'
    ];

    kanbanEvents.forEach(function(evt){
      dpOn(evt, function(){
        // If Kanban panel is visible, refresh it silently
        try{
          var kanbanPanel = document.getElementById('jsPanel');
          if(kanbanPanel && kanbanPanel.style.display === 'block'){
            if(typeof jsLoad === 'function') jsLoad();
          }
        } catch(e){}
      });
    });

    // ═══════════════════════════════════════════════════
    // B. DASHBOARD AUTO-REFRESH
    // ═══════════════════════════════════════════════════
    var dashboardEvents = [
      'job.created', 'job.updated', 'job.completed',
      'invoice.created', 'invoice.paid', 'stock.added',
      'stock.adjusted', 'stock.low', 'customer.created',
      'expense.created', 'quote.created', 'quote.accepted'
    ];

    var _dashboardRefreshScheduled = false;
    function scheduleDashboardRefresh(){
      // Debounce so rapid events don't cause 5 reloads in 1 second
      if(_dashboardRefreshScheduled) return;
      _dashboardRefreshScheduled = true;
      setTimeout(function(){
        _dashboardRefreshScheduled = false;
        var dash = document.getElementById('dashboard');
        if(dash && dash.classList.contains('active')){
          try{
            if(typeof loadDashboard === 'function') loadDashboard();
          } catch(e){}
        }
      }, 600);
    }

    dashboardEvents.forEach(function(evt){
      dpOn(evt, scheduleDashboardRefresh);
    });

    // Also refresh Dashboard when user navigates to it (catch up)
    document.addEventListener('click', function(e){
      var el = e.target.closest('.bnav-item, .tile');
      if(el){
        setTimeout(function(){
          var dash = document.getElementById('dashboard');
          if(dash && dash.classList.contains('active')){
            if(typeof loadDashboard === 'function') loadDashboard();
          }
        }, 200);
      }
    });

    // ═══════════════════════════════════════════════════
    // D. FULL CHAIN — QC PASS → INVOICE → NOTIFY → REMINDER
    // ═══════════════════════════════════════════════════
    dpOn('job.qc_passed', async function(payload){
      // QC passed means the job is ready for pickup. Do 3 things:
      // 1. Auto-generate invoice
      // 2. Offer to notify customer via WhatsApp
      // 3. Schedule 6-month reminder

      // Wait a moment for backend to settle
      await new Promise(function(r){ setTimeout(r, 800); });

      // Show a smart action card
      _showQCCompleteCard(payload);

      // Fire 6-month reminder event
      try{
        dpEmit('reminder.scheduled', {
          job_id: payload.id || payload.job_id,
          months: 6,
          source: 'auto_from_qc'
        });
      } catch(e){}
    });

    function _showQCCompleteCard(payload){
      // Build a floating card that offers the next actions
      var existing = document.getElementById('qcCompleteCard');
      if(existing) existing.remove();

      var jobId = payload.id || payload.job_id || '';
      var customer = payload.customer || '';
      var vehicle = payload.vehicle || '';
      var phone = payload.phone || '';
      var total = payload.total || 0;

      var card = document.createElement('div');
      card.id = 'qcCompleteCard';
      card.style.cssText =
        'position:fixed;bottom:100px;left:16px;right:16px;max-width:420px;' +
        'margin:0 auto;background:linear-gradient(180deg,#10b981,#047857);' +
        'color:#fff;padding:18px;border-radius:16px;z-index:9997;' +
        'box-shadow:0 12px 40px rgba(16,185,129,.5);' +
        'animation:qcSlide 0.4s cubic-bezier(.16,1,.3,1);';

      card.innerHTML =
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">' +
          '<div>' +
            '<div style="font-size:11px;letter-spacing:.1em;opacity:.9;">QC COMPLETE</div>' +
            '<div style="font-size:16px;font-weight:800;margin-top:2px;">' +
              (vehicle || ('Job #' + jobId)) +
            '</div>' +
            (customer ? '<div style="font-size:13px;margin-top:2px;opacity:.9;">' + customer + '</div>' : '') +
          '</div>' +
          '<button onclick="document.getElementById(\'qcCompleteCard\').remove()" ' +
            'style="background:rgba(0,0,0,.2);color:#fff;border:none;border-radius:50%;' +
            'width:32px;height:32px;font-size:16px;cursor:pointer;">✕</button>' +
        '</div>' +
        '<div style="font-size:13px;margin-bottom:14px;opacity:.95;">' +
          'Next: notify the customer, generate the invoice, and schedule a 6-month reminder.' +
        '</div>' +
        '<div style="display:flex;gap:6px;flex-wrap:wrap;">' +
          (phone
            ? '<button onclick="dpNotifyCustomer(\'' + _escAttr(customer) + '\',\'' +
              _escAttr(phone) + '\',\'' + _escAttr(vehicle) + '\')" ' +
              'style="flex:1;padding:11px 14px;background:#fff;color:#047857;border:none;' +
              'border-radius:10px;font-weight:800;font-size:13px;cursor:pointer;min-width:120px;">' +
              '📱 WhatsApp Customer</button>'
            : '') +
          '<button onclick="dpGenerateInvoice(\'' + jobId + '\')" ' +
            'style="flex:1;padding:11px 14px;background:rgba(0,0,0,.25);color:#fff;border:none;' +
            'border-radius:10px;font-weight:800;font-size:13px;cursor:pointer;min-width:120px;">' +
            '🧾 Generate Invoice</button>' +
        '</div>';

      document.body.appendChild(card);

      // Auto-dismiss after 45 seconds if user doesn't interact
      setTimeout(function(){
        if(document.getElementById('qcCompleteCard')) card.remove();
      }, 45000);
    }

    function _escAttr(s){
      return String(s || '').replace(/'/g, "&#39;").replace(/"/g, '&quot;');
    }

    // ═══════════════════════════════════════════════════
    // HELPER — WhatsApp customer with ready-for-pickup message
    // ═══════════════════════════════════════════════════
    window.dpNotifyCustomer = function(customer, phone, vehicle){
      var msg = 'Hi ' + (customer || 'there') + ',\n\n' +
        'Your ' + (vehicle || 'vehicle') + ' is ready for collection. ' +
        'All work has been completed and quality-checked.\n\n' +
        'Thanks for choosing our workshop.\n' +
        'Reply here if you need anything else.';

      var cleanPhone = String(phone || '').replace(/\D/g, '');
      var url = cleanPhone
        ? 'https://wa.me/' + cleanPhone + '?text=' + encodeURIComponent(msg)
        : 'https://wa.me/?text=' + encodeURIComponent(msg);

      window.open(url, '_blank');
      dpEmit('customer.notified', { customer: customer, via: 'whatsapp' });
    };

    // ═══════════════════════════════════════════════════
    // HELPER — Generate invoice from current job
    // ═══════════════════════════════════════════════════
    window.dpGenerateInvoice = async function(jobId){
      if(!jobId){ return; }
      try{
        var r = await fetch('/api/workflow/invoice/' + jobId, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ by: 'auto' })
        });
        var d = await r.json();
        if(d.success){
          if(window.dpToast) dpToast('✅ Invoice #' + d.invoice_id + ' generated', 'success');
          dpEmit('invoice.created', { id: d.invoice_id, job_id: jobId });
          var card = document.getElementById('qcCompleteCard');
          if(card) card.remove();
        } else {
          if(window.dpToast) dpToast('Invoice failed: ' + (d.detail || ''), 'error');
        }
      } catch(e){
        if(window.dpToast) dpToast('Network error', 'error');
      }
    };

    // ═══════════════════════════════════════════════════
    // Auto-notify on job.completed (before QC) — subtle toast
    // ═══════════════════════════════════════════════════
    dpOn('job.completed', function(p){
      if(window.dpToast){
        dpToast('✅ Job complete — QC needed', 'info');
      }
    });

    dpOn('job.assigned', function(p){
      if(window.dpToast && p && p.tech){
        dpToast('👷 Assigned to ' + p.tech, 'info');
      }
    });

    dpOn('job.started', function(p){
      if(window.dpToast && p && p.tech){
        dpToast('▶ ' + p.tech + ' started work', 'info');
      }
    });

    // ═══════════════════════════════════════════════════
    // CSS KEYFRAME for the QC card
    // ═══════════════════════════════════════════════════
    var style = document.createElement('style');
    style.textContent =
      '@keyframes qcSlide{' +
        'from{opacity:0;transform:translateY(24px);}' +
        'to{opacity:1;transform:translateY(0);}' +
      '}';
    document.head.appendChild(style);

    console.log('✓ Event handlers active (Kanban + Dashboard + QC chain)');
  });
})();
</script>
"""
