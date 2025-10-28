export interface ToastOptions {
  title?: string;
  description?: string;
  duration?: number; // ms
}

function escapeHtml(s: string | undefined) {
  if (!s) return "";
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export function toast({ title, description, duration = 4000 }: ToastOptions) {
  if (typeof window === "undefined" || !document) return;

  const wrapper = document.createElement("div");
  wrapper.className = "verse-toast-wrapper";
  wrapper.setAttribute("role", "status");

  const inner = document.createElement("div");
  inner.className = "verse-toast";
  inner.innerHTML = `
    <div class="verse-toast-content">
      ${title ? `<strong class="verse-toast-title">${escapeHtml(title)}</strong>` : ""}
      ${description ? `<div class="verse-toast-desc">${escapeHtml(description)}</div>` : ""}
    </div>
  `;

  wrapper.appendChild(inner);
  document.body.appendChild(wrapper);

  // Small entrance animation class for CSS-based transitions (optional)
  requestAnimationFrame(() => wrapper.classList.add("verse-toast-visible"));

  const remove = () => {
    wrapper.classList.remove("verse-toast-visible");
    setTimeout(() => wrapper.remove(), 200);
  };

  if (duration && duration > 0) {
    setTimeout(remove, duration);
  }

  return {
    remove,
  };
}

export default toast;
