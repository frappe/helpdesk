import * as LucideIcons from "lucide-static";

const icons = {};
for (const icon in LucideIcons) {
  let iconSvg = LucideIcons[icon];
  if (icon == "default") {
    continue;
  }

  // set stroke-width to 1.5
  if (iconSvg && iconSvg.includes("stroke-width")) {
    iconSvg = iconSvg.replace(/stroke-width="2"/g, 'stroke-width="1.5"');
  }
  icons[icon] = iconSvg;

  const dashKeys = camelToDash(icon);
  for (const dashKey of dashKeys) {
    if (dashKey !== icon) {
      icons[dashKey] = iconSvg;
    }
  }
}

export default icons;

function camelToDash(key) {
  // barChart2 -> bar-chart-2
  const withNumber = key.replace(/[A-Z0-9]/g, (m) => "-" + m.toLowerCase());
  // barChart2 -> bar-chart2
  const withoutNumber = key.replace(/[A-Z]/g, (m) => "-" + m.toLowerCase());

  if (withNumber !== withoutNumber) {
    // both are required because unplugin icon resolver doesn't put a dash before numbers
    return [withNumber, withoutNumber];
  }
  return [withNumber];
}
