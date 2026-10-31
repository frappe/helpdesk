# Glossary

**Working hours**: the hours of a workday, set per weekday on an SLA policy (HD Service Day: start and end time). Only working hours count towards an SLA: due dates (response by, resolution by), elapsed times (first response, resolution, hold, failed by), ticket analytics and the outside-hours banner all skip holidays, non-workdays and the time outside these hours.

**Break**: an optional pause inside a workday, such as lunch, set as a break start and end on that workday's row. A row has at most one break, which must sit strictly inside its working hours. The break is not working time: the SLA clock stops for it everywhere working hours apply, and a ticket raised during it is raised outside working hours. Open tickets pick up a new or changed break the next time they are updated.
