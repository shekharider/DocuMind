function ConfirmModal({
  open,
  title,
  body,
  onCancel,
  onConfirm,
}) {
  if (!open) {
    return null;
  }

  return (
    <div className="modal-backdrop">
      <div className="confirm-modal">
        <h2>{title}</h2>
        <p>{body}</p>

        <div className="modal-actions">
          <button
            className="modal-cancel-btn"
            onClick={onCancel}
          >
            Cancel
          </button>

          <button
            className="modal-delete-btn"
            onClick={onConfirm}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmModal;
