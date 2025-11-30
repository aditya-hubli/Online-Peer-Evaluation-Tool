import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { projectsAPI, teamsAPI, evaluationsAPI } from '../api';
import { FolderKanban, Users, ClipboardCheck, TrendingUp, ArrowRight, Calendar, AlertCircle, CheckCircle2 } from 'lucide-react';

function Dashboard({ user }) {
  const [stats, setStats] = useState({
    projects: 0,
    teams: 0,
    evaluations: 0,
    pending: 0
  });
  const [recentProjects, setRecentProjects] = useState([]);
  const [pendingEvaluations, setPendingEvaluations] = useState([]);
  const [completedEvaluations, setCompletedEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const promises = [
        projectsAPI.list(),
        teamsAPI.list(),
        evaluationsAPI.list()
      ];

      // OPETSE-13: If user is a student, fetch their pending and completed evaluations
      if (user.role === 'student' && user.id) {
        promises.push(evaluationsAPI.getStudentEvaluations(user.id));
      }

      const results = await Promise.all(promises);
      const [projectsRes, teamsRes, evalsRes, studentEvalsRes] = results;

      let pendingCount = 0;
      if (studentEvalsRes?.data) {
        setPendingEvaluations(studentEvalsRes.data.pending || []);
        setCompletedEvaluations(studentEvalsRes.data.completed || []);
        pendingCount = studentEvalsRes.data.pending_count || 0;
      }

      setStats({
        projects: projectsRes.data.count || 0,
        teams: teamsRes.data.count || 0,
        evaluations: evalsRes.data.count || 0,
        pending: pendingCount
      });

      setRecentProjects((projectsRes.data.projects || []).slice(0, 5));
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <div className="animate-pulse">Loading dashboard...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ marginBottom: '36px' }}>
        <h1 style={{ 
          fontSize: '36px', 
          fontWeight: '800', 
          marginBottom: '8px',
          background: 'linear-gradient(135deg, #e4e4e7 0%, #a1a1aa 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          letterSpacing: '-0.02em'
        }}>
          Welcome back, {user.name}! 👋
        </h1>
        <p style={{ fontSize: '16px', color: '#a1a1aa', fontWeight: '500' }}>
          Here's what's happening with your projects today.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-3" style={{ marginBottom: '40px' }}>
        <div className="card" style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
          color: 'white',
          border: 'none',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ position: 'absolute', top: '-20px', right: '-20px', opacity: 0.2 }}>
            <FolderKanban size={120} />
          </div>
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <div style={{ 
                width: '48px', 
                height: '48px', 
                background: 'rgba(255, 255, 255, 0.2)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backdropFilter: 'blur(10px)'
              }}>
                <FolderKanban size={24} />
              </div>
              <div>
                <p style={{ fontSize: '14px', opacity: 0.9, fontWeight: '600' }}>Total Projects</p>
                <p style={{ fontSize: '36px', fontWeight: '800', lineHeight: '1' }}>{stats.projects}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="card" style={{ 
          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', 
          color: 'white',
          border: 'none',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ position: 'absolute', top: '-20px', right: '-20px', opacity: 0.2 }}>
            <Users size={120} />
          </div>
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <div style={{ 
                width: '48px', 
                height: '48px', 
                background: 'rgba(255, 255, 255, 0.2)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backdropFilter: 'blur(10px)'
              }}>
                <Users size={24} />
              </div>
              <div>
                <p style={{ fontSize: '14px', opacity: 0.9, fontWeight: '600' }}>Active Teams</p>
                <p style={{ fontSize: '36px', fontWeight: '800', lineHeight: '1' }}>{stats.teams}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="card" style={{ 
          background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', 
          color: 'white',
          border: 'none',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ position: 'absolute', top: '-20px', right: '-20px', opacity: 0.2 }}>
            <ClipboardCheck size={120} />
          </div>
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <div style={{ 
                width: '48px', 
                height: '48px', 
                background: 'rgba(255, 255, 255, 0.2)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backdropFilter: 'blur(10px)'
              }}>
                <ClipboardCheck size={24} />
              </div>
              <div>
                <p style={{ fontSize: '14px', opacity: 0.9, fontWeight: '600' }}>Evaluations</p>
                <p style={{ fontSize: '36px', fontWeight: '800', lineHeight: '1' }}>{stats.evaluations}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Projects */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#e4e4e7' }}>
            Recent Projects
          </h2>
          <Link to="/projects" style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px', 
            color: '#a78bfa', 
            fontWeight: '600', 
            fontSize: '14px',
            textDecoration: 'none',
            transition: 'gap 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.gap = '10px'}
          onMouseLeave={(e) => e.currentTarget.style.gap = '6px'}>
            View all <ArrowRight size={16} />
          </Link>
        </div>
        {recentProjects.length === 0 ? (
          <div className="empty-state">
            <p style={{ fontSize: '16px', marginBottom: '8px' }}>No projects yet.</p>
            <p style={{ fontSize: '14px' }}>Create your first project to get started!</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Instructor</th>
                  <th>Status</th>
                  <th>Teams</th>
                </tr>
              </thead>
              <tbody>
                {recentProjects.map((project) => (
                  <tr key={project.id}>
                    <td>
                      <div>
                        <div style={{ fontWeight: '600', color: '#e4e4e7', marginBottom: '4px' }}>
                          {project.title}
                        </div>
                        <div style={{ fontSize: '13px', color: '#a1a1aa' }}>
                          {project.description}
                        </div>
                      </div>
                    </td>
                    <td style={{ fontWeight: '500', color: '#d4d4d8' }}>
                      {project.instructor?.name || 'N/A'}
                    </td>
                    <td>
                      <span className={`badge ${
                        project.status === 'active' ? 'badge-success' : 
                        project.status === 'completed' ? 'badge-info' : 'badge-warning'
                      }`}>
                        {project.status}
                      </span>
                    </td>
                    <td style={{ fontWeight: '600', color: '#a78bfa' }}>
                      {project.teams?.length || 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* OPETSE-13: Student Pending and Completed Evaluations */}
      {user.role === 'student' && (
        <>
          {/* Pending Evaluations */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ 
                  width: '40px', 
                  height: '40px', 
                  background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <AlertCircle size={20} color="white" />
                </div>
                <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#e4e4e7' }}>
                  Pending Evaluations
                  {pendingEvaluations.length > 0 && (
                    <span style={{ 
                      marginLeft: '12px', 
                      fontSize: '14px', 
                      background: '#f59e0b', 
                      color: 'white',
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontWeight: '600'
                    }}>
                      {pendingEvaluations.length}
                    </span>
                  )}
                </h2>
              </div>
            </div>
            {pendingEvaluations.length === 0 ? (
              <div className="empty-state">
                <CheckCircle2 size={48} style={{ color: '#10b981', marginBottom: '12px' }} />
                <p style={{ fontSize: '16px', marginBottom: '8px', color: '#e4e4e7' }}>All caught up!</p>
                <p style={{ fontSize: '14px' }}>You have no pending evaluations at this time.</p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Form</th>
                      <th>Team</th>
                      <th>Teammate to Evaluate</th>
                      <th>Deadline</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingEvaluations.map((pending, idx) => (
                      <tr key={`${pending.form_id}-${pending.evaluatee_id}-${idx}`}>
                        <td>
                          <div style={{ fontWeight: '600', color: '#e4e4e7' }}>
                            {pending.form_title}
                          </div>
                        </td>
                        <td style={{ fontWeight: '500', color: '#d4d4d8' }}>
                          {pending.team_name}
                        </td>
                        <td style={{ color: '#a78bfa' }}>
                          {pending.evaluatee?.name || 'Unknown'}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#fbbf24' }}>
                            <Calendar size={14} />
                            {pending.form_deadline ? new Date(pending.form_deadline).toLocaleDateString() : 'No deadline'}
                          </div>
                        </td>
                        <td>
                          <Link 
                            to={`/evaluations?form=${pending.form_id}&evaluatee=${pending.evaluatee_id}`}
                            className="btn btn-primary"
                            style={{ fontSize: '13px', padding: '6px 12px' }}
                          >
                            Submit
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Completed Evaluations */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ 
                  width: '40px', 
                  height: '40px', 
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <CheckCircle2 size={20} color="white" />
                </div>
                <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#e4e4e7' }}>
                  Completed Evaluations
                </h2>
              </div>
              <Link to="/evaluations" style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '6px', 
                color: '#a78bfa', 
                fontWeight: '600', 
                fontSize: '14px',
                textDecoration: 'none',
                transition: 'gap 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.gap = '10px'}
              onMouseLeave={(e) => e.currentTarget.style.gap = '6px'}>
                View all <ArrowRight size={16} />
              </Link>
            </div>
            {completedEvaluations.length === 0 ? (
              <div className="empty-state">
                <p style={{ fontSize: '16px', marginBottom: '8px' }}>No completed evaluations yet.</p>
                <p style={{ fontSize: '14px' }}>Start evaluating your teammates!</p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Form</th>
                      <th>Team</th>
                      <th>Evaluatee</th>
                      <th>Score</th>
                      <th>Submitted</th>
                    </tr>
                  </thead>
                  <tbody>
                    {completedEvaluations.slice(0, 5).map((evaluation) => (
                      <tr key={evaluation.id}>
                        <td style={{ fontWeight: '600', color: '#e4e4e7' }}>
                          {evaluation.form?.title || 'N/A'}
                        </td>
                        <td style={{ fontWeight: '500', color: '#d4d4d8' }}>
                          {evaluation.team?.name || 'N/A'}
                        </td>
                        <td style={{ color: '#a78bfa' }}>
                          {evaluation.evaluatee?.name || 'Unknown'}
                        </td>
                        <td>
                          <span className="badge badge-success">
                            {evaluation.total_score}
                          </span>
                        </td>
                        <td style={{ fontSize: '13px', color: '#a1a1aa' }}>
                          {evaluation.submitted_at ? new Date(evaluation.submitted_at).toLocaleDateString() : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h2 style={{ fontSize: '22px', fontWeight: '700', marginBottom: '20px', color: '#e4e4e7' }}>
          Quick Actions
        </h2>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {user.role === 'instructor' && (
            <>
              <a href="/projects" className="btn btn-primary">
                <FolderKanban size={16} />
                Create Project
              </a>
              <a href="/teams" className="btn btn-secondary">
                <Users size={16} />
                Manage Teams
              </a>
            </>
          )}
          <a href="/evaluations" className="btn btn-primary">
            <ClipboardCheck size={16} />
            Submit Evaluation
          </a>
          <a href="/reports" className="btn btn-secondary">
            <TrendingUp size={16} />
            View Reports
          </a>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
