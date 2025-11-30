import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api';
import { LogIn, AlertCircle, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

function Login({ onLogin }) {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.login(formData);
      const userData = response.data.user;
      onLogin(userData);
      toast.success('Login successful! Welcome back!');
      setTimeout(() => navigate('/dashboard'), 1000);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Login failed. Please check your credentials.';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ 
      background: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a24 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Decorative elements */}
      <div style={{ 
        position: 'absolute', 
        top: '-100px', 
        right: '-100px', 
        width: '300px', 
        height: '300px',
        background: 'rgba(99, 102, 241, 0.15)',
        borderRadius: '50%',
        filter: 'blur(80px)'
      }} />
      <div style={{ 
        position: 'absolute', 
        bottom: '-100px', 
        left: '-100px', 
        width: '300px', 
        height: '300px',
        background: 'rgba(139, 92, 246, 0.15)',
        borderRadius: '50%',
        filter: 'blur(80px)'
      }} />

      <Card className="w-full max-w-md" style={{ 
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        border: '1px solid rgba(99, 102, 241, 0.3)',
        position: 'relative',
        zIndex: 1,
        background: 'rgba(24, 24, 36, 0.8)',
        backdropFilter: 'blur(20px)'
      }}>
        <CardHeader className="text-center pb-4">
          <div className="mx-auto w-16 h-16 rounded-2xl flex items-center justify-center mb-6" style={{ 
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            boxShadow: '0 10px 25px rgba(99, 102, 241, 0.5)'
          }}>
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-3xl font-bold" style={{ 
            background: 'linear-gradient(135deg, #e4e4e7 0%, #a1a1aa 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            letterSpacing: '-0.02em',
            marginBottom: '8px'
          }}>
            Welcome Back
          </CardTitle>
          <CardDescription className="text-base mt-2" style={{ color: '#a1a1aa', fontWeight: '500' }}>
            Sign in to your Peer Evaluation account
          </CardDescription>
        </CardHeader>
        
        <CardContent style={{ paddingLeft: '40px', paddingRight: '40px' }}>
          {error && (
            <div className="mb-6 flex items-start gap-3 p-4 rounded-xl text-sm" style={{ 
              background: 'rgba(239, 68, 68, 0.15)',
              border: '2px solid rgba(239, 68, 68, 0.3)',
              color: '#fca5a5'
            }}>
              <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
              <p style={{ fontWeight: '600' }}>{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-semibold" style={{ color: '#e4e4e7' }}>
                Email Address
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="student@university.edu"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                disabled={loading}
                className="h-11"
                style={{ 
                  border: '2px solid rgba(99, 102, 241, 0.2)',
                  borderRadius: '10px',
                  fontSize: '14px',
                  background: 'rgba(15, 15, 25, 0.6)',
                  color: '#e4e4e7'
                }}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-semibold" style={{ color: '#e4e4e7' }}>
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                disabled={loading}
                className="h-11"
                style={{ 
                  border: '2px solid rgba(99, 102, 241, 0.2)',
                  borderRadius: '10px',
                  fontSize: '14px',
                  background: 'rgba(15, 15, 25, 0.6)',
                  color: '#e4e4e7'
                }}
              />
            </div>

            <Button 
              type="submit" 
              className="w-full h-11 font-semibold"
              disabled={loading}
              style={{ 
                marginTop: '32px',
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                border: 'none',
                borderRadius: '10px',
                fontSize: '15px',
                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.5)',
                transition: 'all 0.2s',
                color: 'white'
              }}
            >
              <LogIn className="w-4 h-4 mr-2" />
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm" style={{ color: '#a1a1aa', fontWeight: '500' }}>
            Don't have an account?{' '}
            <Link 
              to="/register" 
              style={{ 
                color: '#a78bfa', 
                fontWeight: '700',
                textDecoration: 'none'
              }}
              onMouseEnter={(e) => e.target.style.textDecoration = 'underline'}
              onMouseLeave={(e) => e.target.style.textDecoration = 'none'}
            >
              Register here
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Login;
