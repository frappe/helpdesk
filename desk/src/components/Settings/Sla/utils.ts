export function formatTimeHMS(seconds) {
  const days = Math.floor(seconds / (3600 * 24));
  const hours = Math.floor((seconds % (3600 * 24)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  let formattedTime = "";

  if (days > 0) {
    formattedTime += ` ${days} ${days === 1 ? "day" : "days"}`;
  }

  if (hours > 0) {
    formattedTime += ` ${hours} ${hours === 1 ? "hour" : "hours"}`;
  }

  if (minutes > 0) {
    formattedTime += ` ${minutes} ${minutes === 1 ? "minute" : "minutes"}`;
  }

  if (remainingSeconds > 0) {
    formattedTime += ` ${remainingSeconds} ${remainingSeconds === 1 ? "second" : "seconds"}`;
  }

  return formattedTime.trim();
}
