import json
import os
from datetime import datetime

class AuditLogger:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def log_process(self, filename, results):
        audit_data = {
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "detections": []
        }

        for res in results:
            audit_data["detections"].append({
                "entity_type": res.entity_type,
                "start": res.start,
                "end": res.end,
                "score": res.score
            })

        audit_filename = f"{os.path.splitext(filename)[0]}_audit.json"
        audit_path = os.path.join(self.output_dir, audit_filename)

        with open(audit_path, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=4, ensure_ascii=False)

        return audit_path
