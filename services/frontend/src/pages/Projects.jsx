import { useState, useEffect } from 'react';
import { projectsAPI } from '../api';
import { Plus, Edit, Trash2, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';

function Projects({ user }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    instructor_id: user.id,
    start_date: '',
    end_date: '',
    status: 'active'
  });

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await projectsAPI.list();
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error('Failed to load projects:', error);
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isEditing) {
        await projectsAPI.update(editingId, formData);
        toast.success('Project updated successfully!');
      } else {
        await projectsAPI.create(formData);
        toast.success('Project created successfully!');
      }
      setShowModal(false);
      setIsEditing(false);
      setEditingId(null);
      setFormData({
        title: '',
        description: '',
        instructor_id: user.id,
        start_date: '',
        end_date: '',
        status: 'active'
      });
      loadProjects();
    } catch (error) {
      toast.error(error.response?.data?.detail || `Failed to ${isEditing ? 'update' : 'create'} project`);
    }
  };

  const handleEdit = (project) => {
    setIsEditing(true);
    setEditingId(project.id);
    setFormData({
      title: project.title,
      description: project.description || '',
      instructor_id: user.id,
      start_date: project.start_date || '',
      end_date: project.end_date || '',
      status: project.status
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this project?')) return;
    
    try {
      await projectsAPI.delete(id);
      toast.success('Project deleted successfully!');
      loadProjects();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete project');
    }
  };

  if (loading) {
    return <div className="container"><div className="loading">Loading projects...</div></div>;
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ 
            fontSize: '32px', 
            fontWeight: '800',
            background: 'linear-gradient(135deg, #e4e4e7 0%, #a1a1aa 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            letterSpacing: '-0.02em',
            marginBottom: '6px'
          }}>
            Projects
          </h1>
          <p style={{ fontSize: '15px', color: '#a1a1aa', fontWeight: '500' }}>
            Manage and monitor all your projects
          </p>
        </div>
        {user.role === 'instructor' && (
          <button className="btn btn-primary" onClick={() => {
            setIsEditing(false);
            setEditingId(null);
            setFormData({
              title: '',
              description: '',
              instructor_id: user.id,
              start_date: '',
              end_date: '',
              status: 'active'
            });
            setShowModal(true);
          }}>
            <Plus size={18} />
            Create Project
          </button>
        )}
      </div>

      {projects.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <p style={{ fontSize: '16px', marginBottom: '8px' }}>No projects yet.</p>
            {user.role === 'instructor' && <p style={{ fontSize: '14px' }}>Create your first project to get started!</p>}
          </div>
        </div>
      ) : (
        <div className="grid grid-2">
          {projects.map((project) => (
            <div key={project.id} className="card" style={{ position: 'relative' }}>
              <div style={{ 
                position: 'absolute',
                top: '16px',
                right: '16px'
              }}>
                <span className={`badge ${
                  project.status === 'active' ? 'badge-success' : 
                  project.status === 'completed' ? 'badge-info' : 'badge-warning'
                }`}>
                  {project.status}
                </span>
              </div>
              
              <div style={{ marginBottom: '20px', paddingRight: '100px' }}>
                <h3 style={{ 
                  fontSize: '20px', 
                  fontWeight: '700', 
                  marginBottom: '10px',
                  color: '#e4e4e7'
                }}>
                  {project.title}
                </h3>
                <p style={{ color: '#a1a1aa', fontSize: '14px', lineHeight: '1.6', marginBottom: '16px' }}>
                  {project.description}
                </p>
                <div style={{ 
                  fontSize: '13px', 
                  color: '#d4d4d8',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  padding: '12px',
                  background: 'rgba(15, 15, 25, 0.4)',
                  borderRadius: '10px',
                  border: '1px solid rgba(99, 102, 241, 0.1)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <strong style={{ color: '#e4e4e7', minWidth: '80px' }}>Instructor:</strong> 
                    <span>{project.instructor?.name || 'N/A'}</span>
                  </div>
                  {project.start_date && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Calendar size={14} style={{ marginRight: '4px' }} />
                      <strong style={{ color: '#e4e4e7', minWidth: '80px' }}>Duration:</strong>
                      <span>{project.start_date} to {project.end_date}</span>
                    </div>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <strong style={{ color: '#e4e4e7', minWidth: '80px' }}>Teams:</strong> 
                    <span style={{ fontWeight: '700', color: '#a78bfa' }}>
                      {project.teams?.length || 0}
                    </span>
                  </div>
                </div>
              </div>
              
              {user.role === 'instructor' && (
                <div style={{ display: 'flex', gap: '10px', paddingTop: '16px', borderTop: '2px solid rgba(99, 102, 241, 0.1)' }}>
                  <button className="btn btn-secondary" onClick={() => handleEdit(project)} style={{ flex: 1 }}>
                    <Edit size={16} />
                    Edit
                  </button>
                  <button className="btn btn-danger" onClick={() => handleDelete(project.id)} style={{ flex: 1 }}>
                    <Trash2 size={16} />
                    Delete
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Project Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{isEditing ? 'Edit Project' : 'Create New Project'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="label">Project Title</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., Software Engineering Mini Project"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="label">Description</label>
                <textarea
                  className="textarea"
                  placeholder="Describe the project objectives and requirements"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div className="grid grid-2">
                <div className="form-group">
                  <label className="label">Start Date</label>
                  <input
                    type="date"
                    className="input"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="label">End Date</label>
                  <input
                    type="date"
                    className="input"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="label">Status</label>
                <select
                  className="input"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  required
                >
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                  <option value="archived">Archived</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  {isEditing ? 'Update Project' : 'Create Project'}
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

export default Projects;
