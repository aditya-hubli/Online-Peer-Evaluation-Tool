import { useState, useEffect } from 'react';
import { reportsAPI, projectsAPI, teamsAPI, formsAPI, usersAPI } from '../api';
import { BarChart3, TrendingUp, Award, Download, FileText } from 'lucide-react';
import toast from 'react-hot-toast';

function Reports({ user }) {
  const [activeTab, setActiveTab] = useState('project');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState('csv'); // OPETSE-16: PDF/CSV selector
  
  // Filter options
  const [projects, setProjects] = useState([]);
  const [teams, setTeams] = useState([]);
  const [forms, setForms] = useState([]);
  const [users, setUsers] = useState([]);
  
  const [selectedProject, setSelectedProject] = useState('');
  const [selectedTeam, setSelectedTeam] = useState('');
  const [selectedForm, setSelectedForm] = useState('');
  const [selectedUser, setSelectedUser] = useState('');

  useEffect(() => {
    loadFilterOptions();
  }, []);

  const loadFilterOptions = async () => {
    try {
      const [projectsRes, teamsRes, formsRes, usersRes] = await Promise.all([
        projectsAPI.list(),
        teamsAPI.list(),
        formsAPI.list(),
        usersAPI.list()
      ]);
      
      setProjects(projectsRes.data.projects || []);
      setTeams(teamsRes.data.teams || []);
      setForms(formsRes.data.forms || []);
      setUsers(usersRes.data.data || usersRes.data.users || []);
    } catch (error) {
      console.error('Failed to load filter options:', error);
    }
  };

  const loadReport = async () => {
    setLoading(true);
    setReportData(null); // Clear previous report
    
    try {
      let response;
      console.log('Loading report for tab:', activeTab);
      
      // OPETSE-8: Pass user role for anonymization
      const params = { requester_role: user?.role };
      
      switch (activeTab) {
        case 'project':
          if (!selectedProject) {
            toast.error('Please select a project');
            setLoading(false);
            return;
          }
          console.log('Fetching project report for ID:', selectedProject);
          response = await reportsAPI.project(selectedProject, params);
          break;
        case 'team':
          if (!selectedTeam) {
            toast.error('Please select a team');
            setLoading(false);
            return;
          }
          console.log('Fetching team report for ID:', selectedTeam);
          response = await reportsAPI.team(selectedTeam, params);
          break;
        case 'user':
          if (!selectedUser) {
            toast.error('Please select a user');
            setLoading(false);
            return;
          }
          console.log('Fetching user report for ID:', selectedUser);
          response = await reportsAPI.user(selectedUser, params);
          break;
        case 'form':
          if (!selectedForm) {
            toast.error('Please select a form');
            setLoading(false);
            return;
          }
          console.log('Fetching form report for ID:', selectedForm);
          response = await reportsAPI.form(selectedForm, params);
          break;
        default:
          setLoading(false);
          return;
      }
      
      console.log('Report response:', response);
      console.log('Report data:', response.data);
      console.log('Anonymized:', response.data.anonymized);
      
      // Backend returns { report: {...}, message: "..." }
      // We need to extract the actual report data
      const actualReportData = response.data.report || response.data;
      console.log('Actual report data:', actualReportData);
      
      setReportData(actualReportData);
    } catch (error) {
      console.error('Failed to load report:', error);
      console.error('Error response:', error.response);
      
      let errorMessage = 'Failed to load report';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
      setReportData(null);
    } finally {
      setLoading(false);
    }
  };

  // OPETSE-32 & OPETSE-16: Export report to CSV or PDF
  const exportReport = async () => {
    setExporting(true);
    
    try {
      let response;
      let fileExtension = exportFormat === 'pdf' ? 'pdf' : 'csv';
      let filename = `report.${fileExtension}`;
      const params = { requester_role: user?.role, format: exportFormat };
      
      switch (activeTab) {
        case 'project':
          if (!selectedProject) {
            toast.error('Please select a project');
            setExporting(false);
            return;
          }
          response = await reportsAPI.exportProject(selectedProject, params);
          filename = `project_report_${selectedProject}_${new Date().toISOString().split('T')[0]}.${fileExtension}`;
          break;
        case 'team':
          if (!selectedTeam) {
            toast.error('Please select a team');
            setExporting(false);
            return;
          }
          response = await reportsAPI.exportTeam(selectedTeam, params);
          filename = `team_report_${selectedTeam}_${new Date().toISOString().split('T')[0]}.${fileExtension}`;
          break;
        case 'user':
        case 'form':
          toast.error('Export is currently available for Project and Team reports only.');
          setExporting(false);
          return;
        default:
          setExporting(false);
          return;
      }
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Failed to export report:', error);
      toast.error('Failed to export report. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const renderProjectReport = () => {
    if (!reportData || !reportData.project) return null;

    const stats = reportData.overall_statistics || {};

    return (
      <div>
        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
            {reportData.project?.title || 'N/A'}
          </h3>
          <p style={{ color: '#6b7280', marginBottom: '16px' }}>{reportData.project?.description || ''}</p>
          <div className="grid grid-3">
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>Total Teams</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#4f46e5' }}>
                {stats.total_teams || reportData.total_teams || 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>Total Evaluations</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
                {stats.total_evaluations || reportData.total_evaluations || 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>Avg Score</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#f59e0b' }}>
                {(stats.average_score || reportData.avg_score || 0).toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Teams Performance</h3>
          {reportData.teams && reportData.teams.length > 0 ? (
            <div className="grid grid-2">
              {reportData.teams.map((teamData, idx) => {
                const team = teamData.team || teamData;
                const teamStats = teamData.statistics || {};
                return (
                  <div key={idx} style={{ padding: '12px', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>{team.name}</h4>
                    <div style={{ fontSize: '13px', color: '#6b7280' }}>
                      Members: {teamStats.total_members || team.member_count || 0}
                    </div>
                    <div style={{ fontSize: '13px', color: '#6b7280' }}>
                      Evaluations: {teamStats.total_evaluations || team.evaluation_count || 0}
                    </div>
                    <div style={{ fontSize: '13px', color: '#6b7280' }}>
                      Avg Score: <span style={{ fontWeight: '600', color: '#4f46e5' }}>
                        {(teamStats.average_score || team.avg_score || 0).toFixed(2)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p style={{ color: '#9ca3af' }}>No teams found for this project.</p>
          )}
        </div>
      </div>
    );
  };

  const renderTeamReport = () => {
    if (!reportData || !reportData.team) return null;

    const stats = reportData.statistics || {};

    return (
      <div>
        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
            {reportData.team?.name || 'N/A'}
          </h3>
          <p style={{ color: '#6b7280', marginBottom: '16px' }}>
            Project: {reportData.team?.project?.title || 'N/A'}
          </p>
          <div className="grid grid-2">
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>Total Members</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#4f46e5' }}>
                {stats.total_members || reportData.total_members || 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>Total Evaluations</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
                {stats.total_evaluations || reportData.total_evaluations || 0}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Member Performance</h3>
          {reportData.members && reportData.members.length > 0 ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Member</th>
                  <th>Evaluations Received</th>
                  <th>Average Score</th>
                </tr>
              </thead>
              <tbody>
                {reportData.members.map((memberData, idx) => {
                  const member = memberData.user || memberData;
                  const memberStats = memberData.statistics || memberData;
                  return (
                    <tr key={idx}>
                      <td>{member.name || member.user_name || 'N/A'}</td>
                      <td>{memberStats.evaluations_received || memberStats.evaluation_count || 0}</td>
                      <td>
                        <span style={{ fontWeight: '600', color: '#4f46e5' }}>
                          {(memberStats.average_score || memberStats.avg_score || 0).toFixed(2)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#9ca3af' }}>No members found for this team.</p>
          )}
        </div>
      </div>
    );
  };

  const renderUserReport = () => {
    if (!reportData || !reportData.user) return null;

    return (
      <div>
        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
            {reportData.user?.name || 'N/A'}
          </h3>
          <p style={{ color: '#6b7280', marginBottom: '16px' }}>
            Email: {reportData.user?.email || 'N/A'}
          </p>
          <div className="grid grid-3">
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>Total Teams</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#4f46e5' }}>
                {reportData.total_teams}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>Evaluations Received</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
                {reportData.total_evaluations_received}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>Overall Avg Score</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#f59e0b' }}>
                {reportData.overall_avg_score?.toFixed(2) || 'N/A'}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Performance by Team</h3>
          {reportData.teams && reportData.teams.length > 0 ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Team</th>
                  <th>Project</th>
                  <th>Evaluations</th>
                  <th>Average Score</th>
                </tr>
              </thead>
              <tbody>
                {reportData.teams.map((team, idx) => (
                  <tr key={idx}>
                    <td>{team.team_name}</td>
                    <td>{team.project_name}</td>
                    <td>{team.evaluation_count}</td>
                    <td>
                      <span style={{ fontWeight: '600', color: '#4f46e5' }}>
                        {team.avg_score?.toFixed(2) || 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#9ca3af' }}>No team data found for this user.</p>
          )}
        </div>
      </div>
    );
  };

  const renderFormReport = () => {
    if (!reportData || !reportData.form) return null;

    return (
      <div>
        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
            {reportData.form?.title || 'N/A'}
          </h3>
          <p style={{ color: '#6b7280', marginBottom: '16px' }}>{reportData.form?.description || ''}</p>
          <div className="grid grid-2">
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>Total Uses</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#4f46e5' }}>
                {reportData.total_uses || 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>Max Score</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
                {reportData.form?.max_score || 'N/A'}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Criteria Statistics</h3>
          {reportData.criteria && reportData.criteria.length > 0 ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Criterion</th>
                  <th>Max Points</th>
                  <th>Uses</th>
                  <th>Avg Score</th>
                  <th>Min Score</th>
                  <th>Max Score</th>
                </tr>
              </thead>
              <tbody>
                {reportData.criteria.map((criterion) => (
                  <tr key={criterion.criterion_id}>
                    <td>{criterion.criterion_name}</td>
                    <td>{criterion.max_points}</td>
                    <td>{criterion.use_count}</td>
                    <td>
                      <span style={{ fontWeight: '600', color: '#4f46e5' }}>
                        {criterion.avg_score?.toFixed(2) || 'N/A'}
                      </span>
                    </td>
                    <td>{criterion.min_score ?? 'N/A'}</td>
                    <td>{criterion.max_score ?? 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#9ca3af' }}>No criteria data found for this form.</p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="container">
      <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '24px' }}>Reports & Analytics</h1>

      {/* Tabs */}
      <div style={{ 
        display: 'flex', 
        gap: '12px', 
        marginBottom: '24px',
        borderBottom: '2px solid #e5e7eb',
        paddingBottom: '0'
      }}>
        {[
          { id: 'project', label: 'Project Report', icon: BarChart3 },
          { id: 'team', label: 'Team Report', icon: TrendingUp },
          { id: 'user', label: 'User Report', icon: Award },
          { id: 'form', label: 'Form Report', icon: BarChart3 }
        ].map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setReportData(null);
              }}
              style={{
                padding: '12px 20px',
                background: activeTab === tab.id ? '#4f46e5' : 'transparent',
                color: activeTab === tab.id ? '#fff' : '#6b7280',
                border: 'none',
                borderRadius: '8px 8px 0 0',
                cursor: 'pointer',
                fontWeight: activeTab === tab.id ? '600' : '400',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s'
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Select Filter</h3>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'end' }}>
          {activeTab === 'project' && (
            <div style={{ flex: 1 }}>
              <label className="label">Project</label>
              <select
                className="input"
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
              >
                <option value="">Select a project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.title}
                  </option>
                ))}
              </select>
            </div>
          )}

          {activeTab === 'team' && (
            <div style={{ flex: 1 }}>
              <label className="label">Team</label>
              <select
                className="input"
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value)}
              >
                <option value="">Select a team</option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {activeTab === 'user' && (
            <div style={{ flex: 1 }}>
              <label className="label">User</label>
              <select
                className="input"
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
              >
                <option value="">Select a user</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name} ({user.email})
                  </option>
                ))}
              </select>
            </div>
          )}

          {activeTab === 'form' && (
            <div style={{ flex: 1 }}>
              <label className="label">Evaluation Form</label>
              <select
                className="input"
                value={selectedForm}
                onChange={(e) => setSelectedForm(e.target.value)}
              >
                <option value="">Select a form</option>
                {forms.map((form) => (
                  <option key={form.id} value={form.id}>
                    {form.title}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button className="btn btn-primary" onClick={loadReport} disabled={loading}>
            {loading ? 'Loading...' : 'Generate Report'}
          </button>
          
          {/* OPETSE-16 & OPETSE-32: Export to CSV/PDF buttons with format selector */}
          {reportData && (activeTab === 'project' || activeTab === 'team') && (
            <>
              <select
                className="input"
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value)}
                style={{ width: 'auto', minWidth: '100px' }}
              >
                <option value="csv">CSV</option>
                <option value="pdf">PDF</option>
              </select>
              
              <button 
                className="btn" 
                onClick={exportReport} 
                disabled={exporting}
                style={{
                  background: '#10b981',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                {exportFormat === 'pdf' ? <FileText size={16} /> : <Download size={16} />}
                {exporting ? 'Exporting...' : `Export ${exportFormat.toUpperCase()}`}
              </button>
            </>
          )}
        </div>
      </div>

      {/* OPETSE-14: Weighted Scoring Notice */}
      {reportData && reportData.weighted_scoring_applied && (
        <div style={{
          padding: '12px 16px',
          background: '#f3e8ff',
          border: '1px solid #c084fc',
          borderRadius: '8px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: '#7c3aed'
        }}>
          <span style={{ fontWeight: '600' }}>★</span>
          <span style={{ fontSize: '14px' }}>
            This report includes weighted scoring - criteria are weighted according to rubric configuration.
          </span>
        </div>
      )}

      {/* Report Content */}
      {loading ? (
        <div className="card">
          <div className="loading">Loading report data...</div>
        </div>
      ) : reportData ? (
        <>
          {activeTab === 'project' && renderProjectReport()}
          {activeTab === 'team' && renderTeamReport()}
          {activeTab === 'user' && renderUserReport()}
          {activeTab === 'form' && renderFormReport()}
        </>
      ) : (
        <div className="card">
          <div className="empty-state">
            <p>Select a filter and click "Generate Report" to view analytics.</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Reports;
