import json
from pathlib import Path
import tools.report_tool as rt
p = Path(__file__).resolve().parents[1] / 'z_扣子api.py'
print(json.dumps(rt.parse_config_from_source(p), ensure_ascii=False, indent=2))
