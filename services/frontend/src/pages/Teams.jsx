import { useState, useEffect } from 'react';
import { teamsAPI, projectsAPI, usersAPI } from '../api';
import { Plus, Users as UsersIcon, Trash2, Edit, MessageCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import TeamChat from '../components/TeamChat';

function Teams({ user }) {
  const [teams, setTeams] = useState([]);
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    project_id: '',
    name: '',
    member_ids: []
  });
  const [chatTeam, setChatTeam] = useState(null);
  const [showChat, setShowChat] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [teamsRes, projectsRes, usersRes] = await Promise.all([
        teamsAPI.list(),
        projectsAPI.list(),
        usersAPI.list()
      ]);
      
      setTeams(teamsRes.data.teams || []);
      setProjects(projectsRes.data.projects || []);
      // Fix: users API returns { success, data: [...] } not { users: [...] }
      const allUsers = usersRes.data.data || usersRes.data.users || usersRes.data || [];
      setUsers(allUsers.filter(u => u.role === 'student'));
      console.log('Loaded users:', allUsers.filter(u => u.role === 'student'));
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load teams');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isEditing) {
        // For update, we need to send name and member_ids
        await teamsAPI.update(editingId, {
          name: formData.name,
          member_ids: formData.member_ids
        });
        toast.success('Team updated successfully!');
      } else {
        await teamsAPI.create(formData);
        toast.success('Team created successfully!');
      }
      setShowModal(false);
      setIsEditing(false);
      setEditingId(null);
      setFormData({ project_id: '', name: '', member_ids: [] });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || `Failed to ${isEditing ? 'update' : 'create'} team`);
    }
  };

  const handleEdit = (team) => {
    setIsEditing(true);
    setEditingId(team.id);
    setFormData({
      project_id: team.project?.id || '',
      name: team.name,
      member_ids: team.members?.map(m => m.id) || []
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this team?')) return;
    
    try {
      await teamsAPI.delete(id);
      toast.success('Team deleted successfully!');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete team');
    }
  };

  const toggleMember = (userId) => {
    setFormData(prev => ({
      ...prev,
      member_ids: prev.member_ids.includes(userId)
        ? prev.member_ids.filter(id => id !== userId)
        : [...prev.member_ids, userId]
    }));
  };

  const isTeamMember = (team) => {
    return team.members?.some(member => member.id === user.id);
  };

  const handleOpenChat = (team) => {
    setChatTeam(team);
    setShowChat(true);
  };

  const handleCloseChat = () => {
    setShowChat(false);
    setChatTeam(null);
  };

  if (loading) {
    return <div className="container"><div className="loading">Loading teams...</div></div>;
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700' }}>Teams</h1>
        {user.role === 'instructor' && (
          <button className="btn btn-primary" onClick={() => {
            setIsEditing(false);
            setEditingId(null);
            setFormData({ project_id: '', name: '', member_ids: [] });
            setShowModal(true);
          }}>
            <Plus size={16} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
            Create Team
          </button>
        )}
      </div>

      {teams.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <p>No teams yet.</p>
            {user.role === 'instructor' && <p>Create your first team to get started!</p>}
          </div>
        </div>
      ) : (
        <div className="grid grid-3">
          {teams.map((team) => (
            <div key={team.id} className="card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <div style={{ 
                  width: '48px', 
                  height: '48px', 
                  borderRadius: '50%', 
                  background: '#e0e7ff', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center'
                }}>
                  <UsersIcon size={24} color="#4f46e5" />
                </div>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600' }}>{team.name}</h3>
                  <p style={{ fontSize: '13px', color: '#6b7280' }}>
                    {team.project?.title || 'No project'}
                  </p>
                </div>
              </div>

              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '13px', fontWeight: '500', color: '#6b7280', marginBottom: '8px' }}>
                  Members ({team.members?.length || 0}):
                </div>
                {team.members && team.members.length > 0 ? (
                  <div style={{ fontSize: '13px' }}>
                    {team.members.map((member, idx) => (
                      <div key={idx} style={{ padding: '4px 0', color: '#374151' }}>
                        • {member.name}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ fontSize: '13px', color: '#9ca3af' }}>No members yet</p>
                )}
              </div>

              {/* Action buttons */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', paddingTop: '12px', borderTop: '1px solid #e5e7eb' }}>
                {/* Chat button - visible to team members */}
                {user.role === 'student' && isTeamMember(team) && (
                  <button 
                    className="btn btn-primary" 
                    onClick={() => handleOpenChat(team)}
                    style={{ width: '100%', padding: '8px' }}
                  >
                    <MessageCircle size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                    Team Chat
                  </button>
                )}

                {/* Edit/Delete buttons - visible to instructors */}
                {user.role === 'instructor' && (
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn btn-secondary" onClick={() => handleEdit(team)} style={{ flex: 1, padding: '8px' }}>
                      <Edit size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                      Edit
                    </button>
                    <button className="btn btn-danger" onClick={() => handleDelete(team.id)} style={{ flex: 1, padding: '8px' }}>
                      <Trash2 size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Team Chat Modal */}
      {showChat && chatTeam && (
        <div className="modal-overlay" onClick={handleCloseChat}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '800px', width: '90%', padding: 0 }}>
            <TeamChat 
              teamId={chatTeam.id}
              teamName={chatTeam.name}
              user={user}
              onClose={handleCloseChat}
            />
          </div>
        </div>
      )}

      {/* Create/Edit Team Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{isEditing ? 'Edit Team' : 'Create New Team'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="label">Team Name</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., Team Alpha"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="label">Project</label>
                <select
                  className="input"
                  value={formData.project_id}
                  onChange={(e) => setFormData({ ...formData, project_id: parseInt(e.target.value) })}
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
                <label className="label">Select Members (Students)</label>
                <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid #d1d5db', borderRadius: '6px', padding: '8px' }}>
                  {users.length === 0 ? (
                    <p style={{ padding: '12px', color: '#9ca3af', textAlign: 'center' }}>
                      No students available. Please create student accounts first.
                    </p>
                  ) : (
                    users.map((student) => (
                      <label key={student.id} style={{ display: 'flex', alignItems: 'center', padding: '8px', cursor: 'pointer', hover: { backgroundColor: '#f3f4f6' } }}>
                        <input
                          type="checkbox"
                          checked={formData.member_ids.includes(student.id)}
                          onChange={() => toggleMember(student.id)}
                          style={{ marginRight: '8px' }}
                        />
                        <span>{student.name} ({student.email})</span>
                      </label>
                    ))
                  )}
                </div>
                <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                  Selected: {formData.member_ids.length} member(s)
                </p>
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  {isEditing ? 'Update Team' : 'Create Team'}
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

export default Teams;
