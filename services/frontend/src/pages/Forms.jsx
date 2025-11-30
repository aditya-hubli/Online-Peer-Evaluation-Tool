import { useState, useEffect } from 'react';
import { formsAPI, projectsAPI } from '../api';
import { Plus, Edit, Trash2, FileText, List, History } from 'lucide-react';  // OPETSE-25: Added History icon
import toast from 'react-hot-toast';

function Forms({ user }) {
  const [forms, setForms] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);  // OPETSE-19: Duplicate modal
  const [duplicatingForm, setDuplicatingForm] = useState(null);  // OPETSE-19: Form being duplicated
  const [duplicateData, setDuplicateData] = useState({ target_project_id: '', new_title: '' });  // OPETSE-19
  const [showVersionModal, setShowVersionModal] = useState(false);  // OPETSE-25: Version history modal
  const [selectedForm, setSelectedForm] = useState(null);  // OPETSE-25: Form for viewing versions
  const [versions, setVersions] = useState([]);  // OPETSE-25: Version list
  const [loadingVersions, setLoadingVersions] = useState(false);  // OPETSE-25: Loading state
  const [formData, setFormData] = useState({
    project_id: '',
    title: '',
    description: '',
    max_score: 100,
    criteria: [{ name: '', description: '', max_points: 10, weight: '', order_index: 0 }]
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [formsRes, projectsRes] = await Promise.all([
        formsAPI.list(),
        projectsAPI.list()
      ]);
      
      setForms(formsRes.data.forms || []);
      setProjects(projectsRes.data.projects || []);
      console.log('Loaded forms:', formsRes.data.forms);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load forms');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate criteria points sum
    const totalPoints = formData.criteria.reduce((sum, c) => sum + parseInt(c.max_points || 0), 0);
    if (totalPoints !== parseInt(formData.max_score)) {
      toast.error(`Criteria points (${totalPoints}) must sum to max score (${formData.max_score})`);
      return;
    }

    // OPETSE-14: Validate weights sum to 100% (if weights are provided)
    const hasWeights = formData.criteria.some(c => c.weight && c.weight !== '');
    if (hasWeights) {
      const totalWeight = formData.criteria.reduce((sum, c) => sum + parseFloat(c.weight || 0), 0);
      if (Math.abs(totalWeight - 100) > 0.01) {
        toast.error(`Criteria weights (${totalWeight.toFixed(2)}%) must sum to exactly 100%`);
        return;
      }
    }

    try {
      const submitData = {
        ...formData,
        project_id: parseInt(formData.project_id),
        max_score: parseInt(formData.max_score),
        criteria: formData.criteria.map((c, idx) => ({
          text: c.name,
          description: c.description,
          max_points: parseInt(c.max_points),
          weight: c.weight && c.weight !== '' ? parseFloat(c.weight) : null,
          order_index: idx
        }))
      };

      if (isEditing) {
        await formsAPI.update(editingId, {
          title: formData.title,
          description: formData.description,
          max_score: parseInt(formData.max_score)
        });
        toast.success('Form updated successfully!');
      } else {
        await formsAPI.create(submitData);
        toast.success('Form created successfully!');
      }
      
      setShowModal(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || `Failed to ${isEditing ? 'update' : 'create'} form`);
    }
  };

  const resetForm = () => {
    setIsEditing(false);
    setEditingId(null);
    setFormData({
      project_id: '',
      title: '',
      description: '',
      max_score: 100,
      criteria: [{ name: '', description: '', max_points: 10, weight: '', order_index: 0 }]
    });
  };

  const handleEdit = (form) => {
    setIsEditing(true);
    setEditingId(form.id);
    setFormData({
      project_id: form.project_id || '',
      title: form.title,
      description: form.description || '',
      max_score: form.max_score,
      criteria: form.criteria.map(c => ({
        name: c.text || c.name,
        description: c.description || '',
        max_points: c.max_points,
        weight: c.weight || '',
        order_index: c.order_index
      }))
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this form?')) return;
    
    try {
      await formsAPI.delete(id);
      toast.success('Form deleted successfully!');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete form');
    }
  };

  // OPETSE-19: Handle form duplication
  const handleDuplicate = (form) => {
    setDuplicatingForm(form);
    setDuplicateData({
      target_project_id: '',
      new_title: `${form.title} (Copy)`
    });
    setShowDuplicateModal(true);
  };

  // OPETSE-25: Handle viewing version history
  const handleViewHistory = async (form) => {
    setSelectedForm(form);
    setShowVersionModal(true);
    setLoadingVersions(true);
    
    try {
      const response = await formsAPI.listVersions(form.id);
      setVersions(response.data.versions || []);
    } catch (error) {
      console.error('Failed to load versions:', error);
      toast.error('Failed to load version history');
      setVersions([]);
    } finally {
      setLoadingVersions(false);
    }
  };

  // OPETSE-25: Handle rollback to a previous version
  const handleRollback = async (versionId) => {
    if (!window.confirm('Are you sure you want to restore this version? Current form will be replaced.')) {
      return;
    }
    
    try {
      await formsAPI.rollback(selectedForm.id, versionId);
      toast.success('Form restored successfully!');
      setShowVersionModal(false);
      loadData();
    } catch (error) {
      console.error('Rollback error:', error);
      toast.error(error.response?.data?.detail || 'Failed to restore form');
    }
  };

  const submitDuplicate = async (e) => {
    e.preventDefault();
    
    if (!duplicateData.target_project_id) {
      toast.error('Please select a target project');
      return;
    }
    
    try {
      await formsAPI.duplicate(duplicatingForm.id, {
        target_project_id: parseInt(duplicateData.target_project_id),
        new_title: duplicateData.new_title || undefined
      });
      toast.success('Form duplicated successfully!');
      setShowDuplicateModal(false);
      setDuplicatingForm(null);
      loadData();
    } catch (error) {
      console.error('Duplicate error:', error);
      toast.error(error.response?.data?.detail || 'Failed to duplicate form');
    }
  };

  const addCriterion = () => {
    setFormData({
      ...formData,
      criteria: [
        ...formData.criteria,
        { name: '', description: '', max_points: 10, weight: '', order_index: formData.criteria.length }
      ]
    });
  };

  const removeCriterion = (index) => {
    if (formData.criteria.length <= 1) {
      toast.error('Form must have at least one criterion');
      return;
    }
    setFormData({
      ...formData,
      criteria: formData.criteria.filter((_, idx) => idx !== index)
    });
  };

  const updateCriterion = (index, field, value) => {
    const newCriteria = [...formData.criteria];
    newCriteria[index][field] = value;
    setFormData({ ...formData, criteria: newCriteria });
  };

  if (loading) {
    return <div className="container"><div className="loading">Loading forms...</div></div>;
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700' }}>Evaluation Forms</h1>
        {user.role === 'instructor' && (
          <button className="btn btn-primary" onClick={() => {
            resetForm();
            setShowModal(true);
          }}>
            <Plus size={16} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
            Create Form
          </button>
        )}
      </div>

      {forms.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <p>No evaluation forms yet.</p>
            {user.role === 'instructor' && <p>Create your first evaluation form to get started!</p>}
          </div>
        </div>
      ) : (
        <div className="grid grid-2">
          {forms.map((form) => (
            <div key={form.id} className="card">
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'start', gap: '12px', marginBottom: '12px' }}>
                  <div style={{ 
                    width: '40px', 
                    height: '40px', 
                    borderRadius: '8px', 
                    background: '#dbeafe', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <FileText size={20} color="#3b82f6" />
                  </div>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '4px' }}>
                      {form.title}
                    </h3>
                    <p style={{ fontSize: '13px', color: '#6b7280' }}>
                      {form.project?.title || 'No project'}
                    </p>
                  </div>
                </div>
                
                <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '12px' }}>
                  {form.description || 'No description'}
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                  <div style={{ padding: '8px', background: '#f3f4f6', borderRadius: '6px' }}>
                    <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '2px' }}>Max Score</div>
                    <div style={{ fontSize: '16px', fontWeight: '600', color: '#4f46e5' }}>
                      {form.max_score}
                    </div>
                  </div>
                  <div style={{ padding: '8px', background: '#f3f4f6', borderRadius: '6px' }}>
                    <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '2px' }}>Criteria</div>
                    <div style={{ fontSize: '16px', fontWeight: '600', color: '#10b981' }}>
                      {form.criteria_count || form.criteria?.length || 0}
                    </div>
                  </div>
                </div>

                {form.criteria && form.criteria.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontSize: '13px', fontWeight: '500', color: '#6b7280', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <List size={14} />
                      Criteria:
                    </div>
                    <div style={{ fontSize: '12px' }}>
                      {form.criteria.slice(0, 3).map((criterion, idx) => (
                        <div key={idx} style={{ padding: '4px 0', color: '#374151', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span>• {criterion.text || criterion.name}</span>
                          <span style={{ fontWeight: '600', color: '#6b7280', whiteSpace: 'nowrap' }}>
                            {criterion.weight ? (
                              <span style={{ color: '#8b5cf6', marginRight: '4px' }}>{criterion.weight}%</span>
                            ) : null}
                            ({criterion.max_points} pts)
                          </span>
                        </div>
                      ))}
                      {form.criteria.length > 3 && (
                        <div style={{ padding: '4px 0', color: '#9ca3af', fontStyle: 'italic' }}>
                          + {form.criteria.length - 3} more...
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
              
              {user.role === 'instructor' && (
                <div style={{ display: 'flex', gap: '8px', paddingTop: '12px', borderTop: '1px solid #e5e7eb' }}>
                  <button className="btn btn-secondary" onClick={() => handleEdit(form)} style={{ flex: 1 }}>
                    <Edit size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                    Edit
                  </button>
                  <button className="btn btn-primary" onClick={() => handleViewHistory(form)} style={{ flex: 1 }} title="View version history and restore previous versions">
                    <History size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                    History
                  </button>
                  <button className="btn btn-primary" onClick={() => handleDuplicate(form)} style={{ flex: 1 }} title="Duplicate this form to reuse as template">
                    <FileText size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                    Duplicate
                  </button>
                  <button className="btn btn-danger" onClick={() => handleDelete(form.id)} style={{ flex: 1 }}>
                    <Trash2 size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                    Delete
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Form Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <h2 className="modal-title">{isEditing ? 'Edit Evaluation Form' : 'Create New Evaluation Form'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="label">Form Title</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., Peer Evaluation Form - Sprint 1"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="label">Project</label>
                <select
                  className="input"
                  value={formData.project_id}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  required
                  disabled={isEditing}
                >
                  <option value="">Select a project</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.title}
                    </option>
                  ))}
                </select>
                {isEditing && (
                  <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                    Project cannot be changed when editing
                  </p>
                )}
              </div>

              <div className="form-group">
                <label className="label">Description (Optional)</label>
                <textarea
                  className="textarea"
                  placeholder="Describe the purpose of this evaluation form..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label className="label">Maximum Score</label>
                <input
                  type="number"
                  className="input"
                  placeholder="100"
                  value={formData.max_score}
                  onChange={(e) => setFormData({ ...formData, max_score: e.target.value })}
                  min="1"
                  required
                />
                <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                  Total of all criteria max points must equal this value
                </p>
              </div>

              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <label className="label" style={{ margin: 0 }}>Evaluation Criteria</label>
                  <button type="button" className="btn btn-secondary" onClick={addCriterion} style={{ padding: '4px 12px', fontSize: '13px' }}>
                    <Plus size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                    Add Criterion
                  </button>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {formData.criteria.map((criterion, index) => (
                    <div key={index} style={{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '12px', background: '#f9fafb' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '13px', fontWeight: '600', color: '#6b7280' }}>
                          Criterion {index + 1}
                        </span>
                        {formData.criteria.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeCriterion(index)}
                            style={{ 
                              background: 'none', 
                              border: 'none', 
                              color: '#ef4444', 
                              cursor: 'pointer',
                              fontSize: '12px',
                              padding: '4px 8px'
                            }}
                          >
                            Remove
                          </button>
                        )}
                      </div>
                      
                      <input
                        type="text"
                        className="input"
                        placeholder="Criterion name (e.g., Communication Skills)"
                        value={criterion.name}
                        onChange={(e) => updateCriterion(index, 'name', e.target.value)}
                        required
                        style={{ marginBottom: '8px' }}
                      />
                      
                      <textarea
                        className="textarea"
                        placeholder="Description (optional)"
                        value={criterion.description}
                        onChange={(e) => updateCriterion(index, 'description', e.target.value)}
                        rows="2"
                        style={{ marginBottom: '8px' }}
                      />
                      
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                        <div>
                          <input
                            type="number"
                            className="input"
                            placeholder="Max points"
                            value={criterion.max_points}
                            onChange={(e) => updateCriterion(index, 'max_points', e.target.value)}
                            min="1"
                            required
                          />
                        </div>
                        <div>
                          <input
                            type="number"
                            className="input"
                            placeholder="Weight % (optional)"
                            value={criterion.weight}
                            onChange={(e) => updateCriterion(index, 'weight', e.target.value)}
                            min="0"
                            max="100"
                            step="0.01"
                            style={{ borderColor: criterion.weight && (parseFloat(criterion.weight) < 0 || parseFloat(criterion.weight) > 100) ? '#ef4444' : undefined }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div style={{ fontSize: '12px', marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <p style={{ color: '#6b7280' }}>
                    Points total: {formData.criteria.reduce((sum, c) => sum + parseInt(c.max_points || 0), 0)} / {formData.max_score}
                  </p>
                  {(() => {
                    const totalWeight = formData.criteria.reduce((sum, c) => sum + parseFloat(c.weight || 0), 0);
                    const hasWeights = formData.criteria.some(c => c.weight && c.weight !== '');
                    if (hasWeights) {
                      const isValid = Math.abs(totalWeight - 100) < 0.01;
                      return (
                        <p style={{ color: isValid ? '#10b981' : '#ef4444', fontWeight: '500' }}>
                          Weights total: {totalWeight.toFixed(2)}% / 100% {isValid ? '✓' : '✗'}
                        </p>
                      );
                    }
                    return (
                      <p style={{ color: '#9ca3af', fontStyle: 'italic' }}>
                        💡 Add weights to enable weighted scoring (must sum to 100%)
                      </p>
                    );
                  })()}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  {isEditing ? 'Update Form' : 'Create Form'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* OPETSE-19: Duplicate Form Modal */}
      {showDuplicateModal && duplicatingForm && (
        <div className="modal-overlay" onClick={() => setShowDuplicateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
              Duplicate Form as Template
            </h2>
            
            <div style={{ background: '#f3f4f6', padding: '12px', borderRadius: '8px', marginBottom: '20px' }}>
              <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>Duplicating:</div>
              <div style={{ fontSize: '15px', fontWeight: '600', color: '#1f2937' }}>{duplicatingForm.title}</div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                {duplicatingForm.criteria_count || duplicatingForm.criteria?.length || 0} criteria • {duplicatingForm.max_score} points
              </div>
            </div>

            <form onSubmit={submitDuplicate}>
              <div className="form-group">
                <label className="label">Target Project *</label>
                <select
                  className="input"
                  value={duplicateData.target_project_id}
                  onChange={(e) => setDuplicateData({ ...duplicateData, target_project_id: e.target.value })}
                  required
                >
                  <option value="">Select project to duplicate form into</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.title}
                    </option>
                  ))}
                </select>
                <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                  The form will be duplicated with all its criteria
                </p>
              </div>

              <div className="form-group">
                <label className="label">New Form Title (Optional)</label>
                <input
                  type="text"
                  className="input"
                  placeholder={`${duplicatingForm.title} (Copy)`}
                  value={duplicateData.new_title}
                  onChange={(e) => setDuplicateData({ ...duplicateData, new_title: e.target.value })}
                />
                <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                  Leave blank to use "{duplicatingForm.title} (Copy)"
                </p>
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  <FileText size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                  Duplicate Form
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowDuplicateModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* OPETSE-25: Version History Modal */}
      {showVersionModal && selectedForm && (
        <div className="modal-overlay" onClick={() => setShowVersionModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <h2 className="modal-title">Version History</h2>
              <button className="modal-close" onClick={() => setShowVersionModal(false)}>×</button>
            </div>
            
            <div style={{ background: '#f3f4f6', padding: '12px', borderRadius: '8px', marginBottom: '20px' }}>
              <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>Form:</div>
              <div style={{ fontSize: '15px', fontWeight: '600', color: '#1f2937' }}>{selectedForm.title}</div>
            </div>

            {loadingVersions ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
                Loading version history...
              </div>
            ) : versions.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
                <History size={48} style={{ opacity: 0.3, marginBottom: '12px' }} />
                <p>No version history yet</p>
                <p style={{ fontSize: '13px', marginTop: '8px' }}>
                  Versions are created automatically when you edit the form
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {versions.map((version) => (
                  <div key={version.id} style={{ 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '8px', 
                    padding: '16px',
                    background: 'white'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
                          Version {version.version_number}
                        </div>
                        <div style={{ fontSize: '12px', color: '#6b7280' }}>
                          {new Date(version.created_at).toLocaleString()}
                        </div>
                      </div>
                      <button 
                        className="btn btn-primary" 
                        onClick={() => handleRollback(version.id)}
                        style={{ padding: '6px 12px', fontSize: '13px' }}
                      >
                        Restore
                      </button>
                    </div>
                    
                    <div style={{ fontSize: '13px', color: '#374151', marginBottom: '8px' }}>
                      <strong>{version.title}</strong>
                    </div>
                    
                    <div style={{ display: 'flex', gap: '12px', fontSize: '12px', color: '#6b7280' }}>
                      <span>📊 {version.max_score} points</span>
                      <span>📋 {version.criteria_count} criteria</span>
                      {version.created_by_email && (
                        <span>👤 {version.created_by_email}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginTop: '20px', padding: '12px', background: '#fef3c7', borderRadius: '8px', fontSize: '13px', color: '#92400e' }}>
              ⚠️ <strong>Note:</strong> Restoring a version will replace the current form and all its criteria. This action creates a new version snapshot before restoring.
            </div>

            <div style={{ marginTop: '16px' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowVersionModal(false)} style={{ width: '100%' }}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Forms;
