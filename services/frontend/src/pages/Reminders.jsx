import { useState, useEffect } from 'react';
import { remindersAPI } from '../api';
import { Bell, Send, Clock, Users, Mail } from 'lucide-react';

function Reminders({ user }) {
  const [upcomingDeadlines, setUpcomingDeadlines] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [hoursAhead, setHoursAhead] = useState(48);
  const [testEmail, setTestEmail] = useState(user?.email || '');
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadUpcomingDeadlines();
    loadStats();
  }, [hoursAhead]);

  const loadUpcomingDeadlines = async () => {
    setLoading(true);
    try {
      const response = await remindersAPI.getUpcomingDeadlines(hoursAhead);
      setUpcomingDeadlines(response.data.forms || []);
    } catch (error) {
      console.error('Failed to load upcoming deadlines:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await remindersAPI.getStats(hoursAhead);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleTriggerReminders = async (formId = null) => {
    setSending(true);
    setMessage('');
    try {
      const payload = formId ? { form_id: formId, hours_ahead: hoursAhead } : { hours_ahead: hoursAhead };
      const response = await remindersAPI.trigger(payload);
      
      if (formId) {
        setMessage(`✅ Sent ${response.data.result.success_count} reminders for this form`);
      } else {
        setMessage(`✅ Sent ${response.data.summary.total_success} reminders across ${response.data.summary.total_forms} forms`);
      }
      
      loadStats(); // Refresh stats
    } catch (error) {
      setMessage('❌ Failed to send reminders: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSending(false);
    }
  };

  const handleSendTestEmail = async () => {
    if (!testEmail) {
      setMessage('❌ Please enter an email address');
      return;
    }
    
    setSending(true);
    setMessage('');
    try {
      await remindersAPI.sendTestEmail(testEmail);
      setMessage('✅ Test email sent successfully! Check your inbox.');
    } catch (error) {
      setMessage('❌ Failed to send test email: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSending(false);
    }
  };

  const isInstructor = user?.role === 'instructor' || user?.role === 'admin';

  return (
    <div className="container">
      <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '24px' }}>
        <Bell size={32} style={{ display: 'inline', marginRight: '12px', verticalAlign: 'middle' }} />
        Deadline Reminders
      </h1>

      {/* Time Window Selector */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
          <Clock size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
          Time Window
        </h3>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <label className="label">Look ahead (hours):</label>
          <select
            className="input"
            value={hoursAhead}
            onChange={(e) => setHoursAhead(parseInt(e.target.value))}
            style={{ width: '150px' }}
          >
            <option value={24}>24 hours</option>
            <option value={48}>48 hours</option>
            <option value={72}>72 hours</option>
            <option value={168}>1 week</option>
          </select>
        </div>
      </div>

      {/* Statistics Card */}
      {stats && (
        <div className="card" style={{ marginBottom: '24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Reminder Statistics</h3>
          <div className="grid grid-3">
            <div>
              <div style={{ fontSize: '13px', opacity: 0.9 }}>Forms with Deadlines</div>
              <div style={{ fontSize: '32px', fontWeight: '700' }}>{stats.total_forms}</div>
            </div>
            <div>
              <div style={{ fontSize: '13px', opacity: 0.9 }}>Students to Remind</div>
              <div style={{ fontSize: '32px', fontWeight: '700' }}>{stats.total_students}</div>
            </div>
            <div>
              <div style={{ fontSize: '13px', opacity: 0.9 }}>Time Window</div>
              <div style={{ fontSize: '32px', fontWeight: '700' }}>{stats.hours_ahead}h</div>
            </div>
          </div>
        </div>
      )}

      {/* Message Display */}
      {message && (
        <div className="card" style={{ 
          marginBottom: '24px', 
          background: message.includes('✅') ? '#d1fae5' : '#fee2e2',
          border: `1px solid ${message.includes('✅') ? '#10b981' : '#ef4444'}`,
          color: message.includes('✅') ? '#065f46' : '#991b1b'
        }}>
          {message}
        </div>
      )}

      {/* Upcoming Deadlines */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600' }}>Upcoming Deadlines</h3>
          {isInstructor && (
            <button 
              className="btn btn-primary"
              onClick={() => handleTriggerReminders()}
              disabled={sending || upcomingDeadlines.length === 0}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <Send size={16} />
              {sending ? 'Sending...' : 'Send All Reminders'}
            </button>
          )}
        </div>

        {loading ? (
          <div className="loading">Loading deadlines...</div>
        ) : upcomingDeadlines.length === 0 ? (
          <div className="empty-state">
            <p>No upcoming deadlines in the next {hoursAhead} hours</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Form Title</th>
                <th>Deadline</th>
                <th>Project ID</th>
                {isInstructor && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {upcomingDeadlines.map((form) => (
                <tr key={form.id}>
                  <td>{form.title}</td>
                  <td>{new Date(form.deadline).toLocaleString()}</td>
                  <td>#{form.project_id}</td>
                  {isInstructor && (
                    <td>
                      <button
                        className="btn"
                        onClick={() => handleTriggerReminders(form.id)}
                        disabled={sending}
                        style={{ fontSize: '13px', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}
                      >
                        <Send size={14} />
                        Send
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Detailed Stats by Form */}
      {stats && stats.forms && stats.forms.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
            <Users size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
            Students to Remind by Form
          </h3>
          <table className="table">
            <thead>
              <tr>
                <th>Form</th>
                <th>Deadline</th>
                <th>Students Pending</th>
              </tr>
            </thead>
            <tbody>
              {stats.forms.map((form) => (
                <tr key={form.form_id}>
                  <td>{form.form_title}</td>
                  <td>{new Date(form.deadline).toLocaleString()}</td>
                  <td>
                    <span style={{ 
                      background: form.students_to_remind > 0 ? '#fef3c7' : '#d1fae5',
                      color: form.students_to_remind > 0 ? '#92400e' : '#065f46',
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontWeight: '600',
                      fontSize: '13px'
                    }}>
                      {form.students_to_remind}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Test Email Section (Instructors Only) */}
      {isInstructor && (
        <div className="card" style={{ marginTop: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
            <Mail size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
            Test Email Configuration
          </h3>
          <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '16px' }}>
            Send a test reminder email to verify your email configuration is working correctly.
          </p>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'end' }}>
            <div style={{ flex: 1 }}>
              <label className="label">Test Email Address</label>
              <input
                type="email"
                className="input"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="email@example.com"
              />
            </div>
            <button
              className="btn"
              onClick={handleSendTestEmail}
              disabled={sending || !testEmail}
              style={{ background: '#10b981', color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <Mail size={16} />
              {sending ? 'Sending...' : 'Send Test Email'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Reminders;
