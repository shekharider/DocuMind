import { useEffect, useRef } from "react";

function SessionMenu({
  session,
  isOpen,
  onOpen,
  onClose,
  onRename,
  onDelete,
}) {
  const menuRef = useRef(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleClickOutside = (e) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target)
      ) {
        onClose();
      }
    };

    document.addEventListener(
      "mousedown",
      handleClickOutside
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );
    };
  }, [isOpen, onClose]);

  return (
    <div
      className="session-menu-wrapper"
      ref={menuRef}
    >
      <button
        className="session-menu-btn"
        onClick={(e) => {
          e.stopPropagation();
          if (isOpen) {
            onClose();
          } else {
            onOpen(session.id);
          }
        }}
        aria-label="Session actions"
      >
        ⋮
      </button>

      {isOpen && (
        <div
          className="session-dropdown"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className="session-dropdown-item"
            onClick={() => {
              onRename(session);
              onClose();
            }}
          >
            Rename
          </button>

          <button
            className="session-dropdown-item danger"
            onClick={() => {
              onDelete(session);
              onClose();
            }}
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
}

export default SessionMenu;
