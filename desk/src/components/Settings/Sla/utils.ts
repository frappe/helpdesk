export function formatTimeHMS(seconds) {
  const days = Math.floor(seconds / (3600 * 24));
  const hours = Math.floor((seconds % (3600 * 24)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  let formattedTime = "";

  if (days > 0) {
    formattedTime += `${days} days `;
  }

  if (hours > 0) {
    formattedTime += `${hours} hours `;
  }

  if (minutes > 0) {
    formattedTime += `${minutes} minutes `;
  }

  if (remainingSeconds > 0) {
    formattedTime += `${remainingSeconds} seconds`;
  }

  return formattedTime.trim();
}
