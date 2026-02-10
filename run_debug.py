import traceback
from anonymizer.pipeline import AnonymizationPipeline

p = AnonymizationPipeline('output')
try:
    p.process_file('input/input.png')
except Exception:
    traceback.print_exc()
    raise
