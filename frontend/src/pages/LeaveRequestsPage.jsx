import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { getLeaveRequests, submitLeaveRequest, reviewLeaveRequest, cancelLeaveRequest, getLeaveBalance } from '../api';

const LEAVE_TYPES = ['pto', 'sick', 'comp', 'unpaid'];

const STATUS_COLORS = {
  pending:   { bg: '#fff3e0', color: '#e65100' },
  approved:  { bg: '#e8f5e9', color: '#2e7d32' },
  denied:    { bg: '#fdecea', color: '#c62828' },
  cancelled: { bg: '#f5f5f5', color: '#757575' },
};

function fmt(d) { return d ? new Date(d).toLocaleDateString() : '—'; }

export default function LeaveRequestsPage() {
  const { token, user, companyId, isManager } = useAuth();
  const [requests, setRequests] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ leave_type: 'pto', start_date: '', end_date: '', days_requested: 1, notes: '' });
  const [reviewId, setReviewId] = useState(null);
  const [reviewForm, setReviewForm] = useState({ status: 'approved', comment: '' });
  const [msg, setMsg] = useState(null);

  const size = 20;

  const load = async () => {
    setLoading(true);
    try {
      const data = await getLeaveRequests(token, page, size);
      setRequests(data.items || []);
      setTotal(data.total || 0);
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => {
    load();
    if (user?.id && companyId) {
      getLeaveBalance(token, user.id, companyId).then(setBalance).catch(() => {});
    }
  }, [token, page]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await submitLeaveRequest(token, { ...form, company_id: companyId });
      setMsg('✅ Leave request submitted');
      setShowForm(false);
      load();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    }
  };

  const handleReview = async (id) => {
    try {
      await reviewLeaveRequest(token, id, reviewForm.status, reviewForm.comment);
      setMsg(`✅ Request ${reviewForm.status}`);
      setReviewId(null);
      load();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    }
  };

  const handleCancel = async (id) => {
    try {
      await cancelLeaveRequest(token, id);
      setMsg('✅ Request cancelled');
      load();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    }
  };

  const pages = Math.ceil(total / size);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0, fontSize: 24, color: '#1a1a2e' }}>Leave Requests</h1>
        <button onClick={() => setShowForm(!showForm)} style={actionBtn}>
          {showForm ? 'Cancel' : '+ New Request'}
        </button>
      </div>

      {/* Balance */}
      {balance && (
        <div style={{ display: 'flex', gap: 12, marginBottom: '1.5rem', flexWrap: 'wrap' }}>
          {[
            { label: 'PTO', total: balance.pto_total, used: balance.pto_used },
            { label: 'Sick', total: balance.sick_total, used: balance.sick_used },
            { label: 'Comp', total: balance.comp_earned, used: balance.comp_used },
          ].map(({ label, total, used }) => (
            <div key={label} style={{ background: '#fff', borderRadius: 8, padding: '0.75rem 1rem', boxShadow: '0 1px 4px rgba(0,0,0,0.07)', minWidth: 130 }}>
              <div style={{ fontWeight: 700, color: '#1565c0', fontSize: 20 }}>{(total - used).toFixed(1)}</div>
              <div style={{ fontSize: 12, color: '#666' }}>{label} days remaining</div>
            </div>
          ))}
        </div>
      )}

      {msg && <div style={{ marginBottom: '1rem', padding: '0.6rem 1rem', background: '#e8f5e9', borderRadius: 6, color: '#2e7d32' }}>{msg}</div>}

      {/* New request form */}
      {showForm && (
        <form onSubmit={handleSubmit} style={{ background: '#fff', borderRadius: 10, padding: '1.25rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.07)' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: 15 }}>New Leave Request</h3>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <div>
              <label style={lbl}>Type</label>
              <select value={form.leave_type} onChange={e => setForm(f => ({ ...f, leave_type: e.target.value }))} style={inp}>
                {LEAVE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label style={lbl}>Start Date</label>
              <input type="date" required value={form.start_date} onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))} style={inp} />
            </div>
            <div>
              <label style={lbl}>End Date</label>
              <input type="date" required value={form.end_date} onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))} style={inp} />
            </div>
            <div>
              <label style={lbl}>Days</label>
              <input type="number" min="0.5" step="0.5" required value={form.days_requested} onChange={e => setForm(f => ({ ...f, days_requested: parseFloat(e.target.value) }))} style={{ ...inp, width: 70 }} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={lbl}>Notes</label>
              <input type="text" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} style={{ ...inp, width: '100%' }} placeholder="Optional notes" />
            </div>
          </div>
          <button type="submit" style={{ ...actionBtn, marginTop: '0.75rem' }}>Submit Request</button>
        </form>
      )}

      {/* Table */}
      <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#1565c0', color: '#fff' }}>
              <th style={th}>Type</th>
              <th style={th}>Start</th>
              <th style={th}>End</th>
              <th style={th}>Days</th>
              <th style={th}>Status</th>
              <th style={th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={6} style={{ padding: '1rem', textAlign: 'center' }}>Loading…</td></tr>}
            {!loading && requests.length === 0 && <tr><td colSpan={6} style={{ padding: '1rem', textAlign: 'center', color: '#999' }}>No leave requests</td></tr>}
            {requests.map(r => (
              <>
                <tr key={r.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={td}><span style={{ fontWeight: 600 }}>{r.leave_type}</span></td>
                  <td style={td}>{fmt(r.start_date)}</td>
                  <td style={td}>{fmt(r.end_date)}</td>
                  <td style={td}>{r.days_requested}</td>
                  <td style={td}>
                    <span style={{ padding: '2px 8px', borderRadius: 10, fontSize: 12, fontWeight: 600, ...(STATUS_COLORS[r.status] || {}) }}>
                      {r.status}
                    </span>
                  </td>
                  <td style={td}>
                    {r.status === 'pending' && !isManager && (
                      <button onClick={() => handleCancel(r.id)} style={smallBtn}>Cancel</button>
                    )}
                    {r.status === 'pending' && isManager && (
                      <button onClick={() => setReviewId(r.id)} style={smallBtn}>Review</button>
                    )}
                  </td>
                </tr>
                {reviewId === r.id && (
                  <tr key={`rev-${r.id}`} style={{ background: '#fffde7' }}>
                    <td colSpan={6} style={{ padding: '1rem' }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                        <div>
                          <label style={{ ...lbl, marginTop: 0 }}>Decision</label>
                          <select value={reviewForm.status} onChange={e => setReviewForm(f => ({ ...f, status: e.target.value }))} style={inp}>
                            <option value="approved">Approve</option>
                            <option value="denied">Deny</option>
                          </select>
                        </div>
                        <div style={{ flex: 1 }}>
                          <label style={{ ...lbl, marginTop: 0 }}>Comment</label>
                          <input type="text" value={reviewForm.comment} onChange={e => setReviewForm(f => ({ ...f, comment: e.target.value }))} style={{ ...inp, width: '100%' }} placeholder="Optional comment" />
                        </div>
                        <button onClick={() => handleReview(r.id)} style={{ ...smallBtn, background: '#1565c0', color: '#fff' }}>Confirm</button>
                        <button onClick={() => setReviewId(null)} style={smallBtn}>Cancel</button>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div style={{ display: 'flex', gap: 8, marginTop: '1rem', justifyContent: 'flex-end' }}>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={pageBtn}>‹ Prev</button>
          <span style={{ lineHeight: '2rem', fontSize: 13 }}>Page {page} of {pages}</span>
          <button onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page === pages} style={pageBtn}>Next ›</button>
        </div>
      )}
    </div>
  );
}

const th = { padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600 };
const td = { padding: '0.65rem 1rem', color: '#333' };
const lbl = { display: 'block', fontSize: 12, fontWeight: 600, color: '#555', marginBottom: 3, marginTop: 8 };
const inp = { padding: '0.45rem 0.6rem', border: '1px solid #ddd', borderRadius: 5, fontSize: 13 };
const smallBtn = { padding: '0.3rem 0.7rem', background: '#f0f0f0', border: '1px solid #ddd', borderRadius: 4, cursor: 'pointer', fontSize: 12 };
const pageBtn = { padding: '0.4rem 0.8rem', background: '#fff', border: '1px solid #ddd', borderRadius: 4, cursor: 'pointer', fontSize: 13 };
const actionBtn = { padding: '0.55rem 1.1rem', background: '#1565c0', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600 };
