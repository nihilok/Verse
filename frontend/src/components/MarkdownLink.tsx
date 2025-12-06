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

/**
 * Creates a MarkdownLink component with a callback that fires on navigation.
 * Useful for closing modals when a link is clicked.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function createMarkdownLinkWithCallback(onNavigate: () => void) {
  return function MarkdownLinkWithCallback({
    href,
    children,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement>) {
    const isInternal = href && (href.startsWith("/") || href.startsWith("?"));

    const handleClick = () => {
      onNavigate();
    };

    if (isInternal) {
      return (
        <Link to={href} onClick={handleClick} {...props}>
          {children}
        </Link>
      );
    }

    return (
      <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
        {children}
      </a>
    );
  };
}
