import { Loader2 } from 'lucide-react';

function LoadingButton({ 
  loading, 
  children, 
  className = 'btn btn-primary', 
  type = 'submit',
  disabled = false,
  onClick,
  ...props 
}) {
  return (
    <button 
      type={type}
      className={className}
      disabled={loading || disabled}
      onClick={onClick}
      style={{
        position: 'relative',
        opacity: loading || disabled ? 0.7 : 1,
        cursor: loading || disabled ? 'not-allowed' : 'pointer',
        ...props.style
      }}
      {...props}
    >
      {loading && (
        <span style={{ 
          marginRight: '8px', 
          display: 'inline-flex', 
          alignItems: 'center' 
        }}>
          <Loader2 size={16} className="animate-spin" style={{ 
            animation: 'spin 1s linear infinite' 
          }} />
        </span>
      )}
      {children}
    </button>
  );
}

export default LoadingButton;
