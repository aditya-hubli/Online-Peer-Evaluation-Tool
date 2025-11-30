import { X } from 'lucide-react';

function ConfirmModal({ show, onConfirm, onCancel, title, message, confirmText = 'Confirm', cancelText = 'Cancel', variant = 'danger' }) {
  if (!show) return null;

  const confirmButtonClass = variant === 'danger' ? 'btn-danger' : 'btn-primary';

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '480px' }}>
        <div className="modal-header">
          <h2 className="modal-title">{title}</h2>
          <button onClick={onCancel} className="modal-close">
            <X size={20} />
          </button>
        </div>
        <div style={{ marginBottom: '28px' }}>
          <p style={{ fontSize: '15px', lineHeight: '1.6', color: '#d4d4d8' }}>
            {message}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button onClick={onCancel} className="btn btn-secondary">
            {cancelText}
          </button>
          <button onClick={onConfirm} className={`btn ${confirmButtonClass}`}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmModal;
