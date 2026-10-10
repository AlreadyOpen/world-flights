"""Where the bake keeps downloads (CACHE) and writes results (OUT). PIPELINE_DATA moves both (default: ./data next to this file)."""
import os
DATA = os.environ.get('PIPELINE_DATA', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
CACHE, OUT = os.path.join(DATA, 'cache'), os.path.join(DATA, 'out')
