from gherkin.parser import Parser
from app.utils.logging_config import logger

def parse_gherkin_text(content: str):
    """
    Utility to convert raw Gherkin string into a structured dict.
    """
    parser = Parser()
    try:
        logger.info("GherkinParser: Parsing raw content...")
        doc = parser.parse(content)
        
        feature = doc.get('feature', {})
        scenarios = []

        for child in feature.get('children', []):
            if 'scenario' in child:
                scen = child['scenario']
                steps = [{"keyword": s['keyword'].strip(), "text": s['text'].strip()} for s in scen.get('steps', [])]
                scenarios.append({
                    "name": scen.get('name'),
                    "steps": steps
                })
        
        return {
            "feature_name": feature.get('name'),
            "scenarios": scenarios
        }
    except Exception as e:
        logger.error(f"GherkinParser Error: {str(e)}")
        return None