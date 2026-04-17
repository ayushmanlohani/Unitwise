/**
 * Date/time formatting utilities
 * Separated for reusability and easy updates
 */

export function formatChatTime(dateString) {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  
  return date.toLocaleTimeString('en-US', { 
    hour: 'numeric', 
    minute: '2-digit',
    hour12: true 
  });
}

export function formatChatDate(dateString) {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  const now = new Date();
  
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  
  const diffDays = Math.floor((nowOnly - dateOnly) / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return 'Today';
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  }
}

export function getSubjectInitials(subject) {
  if (!subject) return '??';
  const cleanSubject = typeof subject === 'string' ? subject.replace(/,/g, ' ') : String(subject);
  const words = cleanSubject.trim().split(/\s+/).filter(w => w.length > 0);
  if (words.length === 0) return '??';
  if (words.length === 1) return words[0].substring(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}