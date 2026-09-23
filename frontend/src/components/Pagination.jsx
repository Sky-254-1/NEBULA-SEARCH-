export function Pagination({ page, pageSize, total, onPageChange, disabled }) {
  if (!total || total <= pageSize) return null;

  const totalPages = Math.ceil(total / pageSize);

  return (
    <nav className="pagination" aria-label="Search results pagination">
      <button
        type="button"
        className="btn ghost"
        disabled={disabled || page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        ← Previous
      </button>
      <span className="pagination-info">
        Page {page} of {totalPages}
      </span>
      <button
        type="button"
        className="btn ghost"
        disabled={disabled || page >= totalPages}
        onClick={() => onPageChange(page + 1)}
      >
        Next →
      </button>
    </nav>
  );
}
