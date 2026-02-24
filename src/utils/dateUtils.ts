// Utility function to get the current month abbreviation (Jan, Feb, Mar, etc.)
export function getCurrentMonthAbbreviation(): string {
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];
  
  const currentDate = new Date();
  const currentMonthIndex = currentDate.getMonth(); // 0 = January, 11 = December
  
  return months[currentMonthIndex];
}

// Utility function to convert month abbreviation to full name
export function getMonthFullName(monthAbbrev: string): string {
  const monthMap: Record<string, string> = {
    'Jan': 'January',
    'Feb': 'February', 
    'Mar': 'March',
    'Apr': 'April',
    'May': 'May',
    'Jun': 'June',
    'Jul': 'July',
    'Aug': 'August',
    'Sep': 'September',
    'Oct': 'October',
    'Nov': 'November',
    'Dec': 'December'
  };
  
  return monthMap[monthAbbrev] || monthAbbrev;
}