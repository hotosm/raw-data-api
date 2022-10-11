  #!/bin/bash
  psql -U postgres  insights < /sql/insights.sql
  psql -U postgres  insights < /sql/mapathon_summary.sql
  psql -U postgres  raw  < /sql/raw_data.sql
  psql -U postgres  underpass < /sql/underpass.sql
  psql -U postgres  tm < /sql/tasking-manager.sql