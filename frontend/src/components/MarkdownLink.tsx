import { Link } from "react-router-dom";
import { AnchorHTMLAttributes } from "react";

/**
 * Custom link component for ReactMarkdown that uses React Router's Link
 * for internal links (preventing page reloads) and regular <a> tags for external links.
 */
export default function MarkdownLink({
  href,
  children,
  ...props
}: AnchorHTMLAttributes<HTMLAnchorElement>) {
  // Check if the link is internal (starts with / or ?)
  const isInternal = href && (href.startsWith("/") || href.startsWith("?"));

  if (isInternal) {
    return (
      <Link to={href} {...props}>
        {children}
      </Link>
    );
  }

  // External link - use regular anchor tag with security attributes
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
      {children}
    </a>
  );
}
