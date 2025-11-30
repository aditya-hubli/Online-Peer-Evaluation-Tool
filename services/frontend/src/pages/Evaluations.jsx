import { useState, useEffect } from 'react';
import { evaluationsAPI, formsAPI, teamsAPI, usersAPI } from '../api';
import { FileText, Send } from 'lucide-react';
import toast from 'react-hot-toast';

function Evaluations({ user }) {
  const [evaluations, setEvaluations] = useState([]);
  const [forms, setForms] = useState([]);
  const [teams, setTeams] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedForm, setSelectedForm] = useState(null);
  const [formData, setFormData] = useState({
    evaluation_form_id: '',
    team_id: '',
    evaluatee_id: '',
    scores: {},
    comments: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (formData.team_id) {
      loadTeamMembers(formData.team_id);
    } else {
      setTeamMembers([]);
    }
  }, [formData.team_id]);

  const loadData = async () => {
    try {
      // OPETSE-8: Pass user role to get properly anonymized data
      const [evaluationsRes, formsRes, teamsRes] = await Promise.all([
        evaluationsAPI.list({ requester_role: user?.role }),
        formsAPI.list(),
        teamsAPI.list()
      ]);
      
      setEvaluations(evaluationsRes.data.evaluations || []);
      setForms(formsRes.data.forms || []);
      setTeams(teamsRes.data.teams || []);
      
      console.log('Loaded forms:', formsRes.data.forms || []);
      console.log('Loaded teams:', teamsRes.data.teams || []);
      console.log('Anonymized:', evaluationsRes.data.anonymized);
    } catch (error) {
      console.error('Failed to load evaluations:', error);
      toast.error('Failed to load evaluations');
    } finally {
      setLoading(false);
    }
  };

  const loadTeamMembers = async (teamId) => {
    try {
      const res = await teamsAPI.get(teamId);
      // API returns { team: {...}, message: "..." }
      const team = res.data.team || res.data;
      setTeamMembers(team.members || []);
      console.log('Loaded team members:', team.members || []);
    } catch (error) {
      console.error('Failed to load team members:', error);
      setTeamMembers([]);
    }
  };

  const loadFormDetails = async (formId) => {
    try {
      const res = await formsAPI.get(formId);
      // API returns { form: {...}, message: "..." }
      const form = res.data.form || res.data;
      setSelectedForm(form);
      
      // Initialize scores object for all criteria
      const initialScores = {};
      (form.criteria || []).forEach(criterion => {
        initialScores[criterion.id] = 0;
      });
      setFormData(prev => ({ ...prev, scores: initialScores }));
    } catch (error) {
      console.error('Failed to load form details:', error);
      alert('Failed to load form criteria');
    }
  };

  const handleFormChange = (formId) => {
    setFormData(prev => ({ ...prev, evaluation_form_id: parseInt(formId) }));
    if (formId) {
      loadFormDetails(formId);
    } else {
      setSelectedForm(null);
    }
  };

  const handleScoreChange = (criterionId, score) => {
    setFormData(prev => ({
      ...prev,
      scores: {
        ...prev.scores,
        [criterionId]: parseInt(score) || 0
      }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // OPETSE-21: Track submission start time for performance monitoring
    const submissionStartTime = performance.now();
    
    // Prepare scores array for API
    const scoresArray = Object.entries(formData.scores).map(([criterion_id, score]) => ({
      criterion_id: parseInt(criterion_id),
      score: parseInt(score)
    }));

    // Calculate total score
    const totalScore = scoresArray.reduce((sum, scoreObj) => sum + scoreObj.score, 0);

    const submitData = {
      form_id: parseInt(formData.evaluation_form_id),  // Backend expects 'form_id'
      evaluator_id: user.id,  // Current user is the evaluator (UUID string)
      evaluatee_id: formData.evaluatee_id,  // Keep as UUID string
      team_id: parseInt(formData.team_id),
      total_score: totalScore,  // Add calculated total score
      scores: scoresArray,
      comments: formData.comments || ''  // Ensure comments is a string
    };

    console.log('Submitting evaluation:', submitData);

    try {
      const response = await evaluationsAPI.create(submitData);
      console.log('Evaluation response:', response);
      
      // OPETSE-21: Calculate and display submission time
      const submissionEndTime = performance.now();
      const submissionTimeMs = submissionEndTime - submissionStartTime;
      const submissionTimeSeconds = (submissionTimeMs / 1000).toFixed(3);
      
      // Get server-side submission time if available
      const serverTime = response.data?.submission_time_seconds || null;
      
      let successMessage = 'Evaluation submitted successfully!';
      if (serverTime !== null) {
        successMessage += `\n\nSubmission completed in ${serverTime}s (server time)`;
        if (submissionTimeSeconds < 2) {
          successMessage += '\n✅ Performance requirement met (< 2 seconds)';
        } else {
          successMessage += `\n⚠️ Submission took ${submissionTimeSeconds}s (client time)`;
        }
      } else {
        successMessage += `\n\nSubmission completed in ${submissionTimeSeconds}s`;
        if (submissionTimeSeconds < 2) {
          successMessage += '\n✅ Performance requirement met (< 2 seconds)';
        }
      }
      
      toast.success(successMessage);
      setShowModal(false);
      setFormData({
        evaluation_form_id: '',
        team_id: '',
        evaluatee_id: '',
        scores: {},
        comments: ''
      });
      setSelectedForm(null);
      loadData();
    } catch (error) {
      console.error('Evaluation submission error:', error);
      console.error('Error response:', error.response?.data);
      
      let errorMessage = 'Failed to submit evaluation';
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map(err => err.msg || JSON.stringify(err)).join(', ');
        } else {
          errorMessage = JSON.stringify(error.response.data.detail);
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return <div className="container"><div className="loading">Loading evaluations...</div></div>;
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700' }}>Evaluations</h1>
        {user.role === 'student' && (
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Send size={16} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
            Submit Evaluation
          </button>
        )}
      </div>

      {evaluations.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <p>No evaluations yet.</p>
            {user.role === 'student' && <p>Submit your first peer evaluation!</p>}
          </div>
        </div>
      ) : (
        <div className="card">
          {user.role === 'student' && (
            <div style={{ padding: '12px', backgroundColor: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '8px', marginBottom: '16px' }}>
              <p style={{ margin: 0, fontSize: '14px', color: '#0c4a6e' }}>
                <strong>OPETSE-8:</strong> For your privacy and honest feedback, evaluator identities are anonymized. 
                Only instructors and admins can see who submitted evaluations.
              </p>
            </div>
          )}
          <table className="table">
            <thead>
              <tr>
                <th>Form</th>
                <th>Team</th>
                <th>Evaluator</th>
                <th>Evaluatee</th>
                <th>Score</th>
                <th>Date</th>
                <th>Comments</th>
              </tr>
            </thead>
            <tbody>
              {evaluations.map((evaluation) => (
                <tr key={evaluation.id}>
                  <td>{evaluation.form?.title || evaluation.evaluation_form?.title || 'N/A'}</td>
                  <td>{evaluation.team?.name || 'N/A'}</td>
                  <td>{evaluation.evaluator?.name || 'N/A'}</td>
                  <td>{evaluation.evaluatee?.name || 'N/A'}</td>
                  <td>
                    <span style={{ fontWeight: '600', color: '#4f46e5' }}>
                      {evaluation.total_score || 0}
                    </span>
                    {evaluation.score_percentage && (
                      <span style={{ fontSize: '11px', color: '#6b7280', marginLeft: '4px' }}>({evaluation.score_percentage}%)</span>
                    )}
                    {evaluation.weighted_scoring_applied && (
                      <span title="Weighted scoring applied" style={{ marginLeft: '4px', color: '#8b5cf6' }}>★</span>
                    )}
                  </td>
                  <td>{formatDate(evaluation.submitted_at || evaluation.created_at)}</td>
                  <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {evaluation.comments || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Submit Evaluation Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <h2 className="modal-title">Submit Peer Evaluation</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="label">Evaluation Form</label>
                <select
                  className="input"
                  value={formData.evaluation_form_id}
                  onChange={(e) => handleFormChange(e.target.value)}
                  required
                >
                  <option value="">Select a form</option>
                  {forms.length === 0 ? (
                    <option disabled>No forms available - Instructor needs to create forms</option>
                  ) : (
                    forms.map((form) => (
                      <option key={form.id} value={form.id}>
                        {form.title}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="form-group">
                <label className="label">Team</label>
                <select
                  className="input"
                  value={formData.team_id}
                  onChange={(e) => setFormData({ ...formData, team_id: parseInt(e.target.value), evaluatee_id: '' })}
                  required
                >
                  <option value="">Select a team</option>
                  {teams.length === 0 ? (
                    <option disabled>No teams available - Instructor needs to create teams</option>
                  ) : (
                    teams.map((team) => (
                      <option key={team.id} value={team.id}>
                        {team.name}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="form-group">
                <label className="label">Evaluate Team Member</label>
                <select
                  className="input"
                  value={formData.evaluatee_id}
                  onChange={(e) => {
                    console.log('Selected evaluatee:', e.target.value);
                    setFormData(prev => ({ ...prev, evaluatee_id: e.target.value }));
                  }}
                  required
                  disabled={!formData.team_id}
                >
                  <option value="">Select a team member</option>
                  {!formData.team_id ? (
                    <option disabled>Please select a team first</option>
                  ) : teamMembers.length === 0 ? (
                    <option disabled>No other team members available</option>
                  ) : (
                    teamMembers
                      .filter(member => member.id !== user.id)
                      .map((member) => (
                        <option key={member.id} value={member.id}>
                          {member.name}
                        </option>
                      ))
                  )}
                </select>
              </div>

              {selectedForm && selectedForm.criteria && selectedForm.criteria.length > 0 && (
                <div className="form-group">
                  <label className="label">Evaluation Criteria</label>
                  <div style={{ border: '1px solid #d1d5db', borderRadius: '6px', padding: '12px' }}>
                    {selectedForm.criteria.map((criterion) => (
                      <div key={criterion.id} style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid #e5e7eb' }}>
                        <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '4px', color: '#374151' }}>
                          {criterion.text || criterion.name}
                          {criterion.weight && (
                            <span style={{ color: '#8b5cf6', fontWeight: '500', fontSize: '13px', marginLeft: '6px' }}>
                              ({criterion.weight}% weight)
                            </span>
                          )}
                          <span style={{ color: '#6b7280', fontWeight: '400', fontSize: '13px', marginLeft: '4px' }}>
                            - Max: {criterion.max_points} pts
                          </span>
                        </label>
                        {criterion.description && (
                          <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px', fontStyle: 'italic' }}>
                            {criterion.description}
                          </p>
                        )}
                        <input
                          type="number"
                          className="input"
                          min="0"
                          max={criterion.max_points}
                          value={formData.scores[criterion.id] || 0}
                          onChange={(e) => handleScoreChange(criterion.id, e.target.value)}
                          required
                          placeholder={`Score (0-${criterion.max_points})`}
                        />
                      </div>
                    ))}
                  </div>
                  <div style={{ fontSize: '12px', marginTop: '8px' }}>
                    <p style={{ color: '#6b7280', marginBottom: '4px' }}>
                      Total Score: {Object.values(formData.scores).reduce((sum, score) => sum + parseInt(score || 0), 0)} / {selectedForm.max_score}
                    </p>
                    {selectedForm.criteria.some(c => c.weight) && (
                      <p style={{ color: '#8b5cf6', fontWeight: '500', fontSize: '11px' }}>
                        ★ Weighted scoring will be applied based on criterion weights
                      </p>
                    )}
                  </div>
                </div>
              )}

              <div className="form-group">
                <label className="label">Comments (Optional)</label>
                <textarea
                  className="textarea"
                  placeholder="Add any additional feedback..."
                  rows="4"
                  value={formData.comments}
                  onChange={(e) => setFormData({ ...formData, comments: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Submit Evaluation
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Evaluations;
