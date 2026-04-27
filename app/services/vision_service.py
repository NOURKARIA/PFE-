import os
from typing import Dict, List, Optional

from app.models.yolo_model import YOLOModelWrapper
from app.utils.image_processing import crop_element, summarize_patch
from app.utils.text_similarity import TextSimilarity


class VisionService:
    def __init__(self):
        model_path = os.path.join("trained_models", "vision", "yolov8_ui_elements2.pt")
        self.model = YOLOModelWrapper(model_path)
        self.class_names = ["button", "input_field", "link", "dropdown", "checkbox"]

    def _resolve_label(self, label_id: int) -> str:
        names = getattr(getattr(self.model, "model", None), "names", {})
        return names.get(label_id, self.class_names[label_id] if label_id < len(self.class_names) else "element")

    @staticmethod
    def _to_coords(raw_coords):
        first = raw_coords[0]
        return first.tolist() if hasattr(first, "tolist") else list(first)

    @staticmethod
    def _sort_elements(elements: List[Dict]) -> List[Dict]:
        return sorted(
            elements,
            key=lambda item: (
                1 if item.get("is_match") else 0,
                item.get("confidence", 0.0),
                len((item.get("text") or "").strip()),
            ),
            reverse=True,
        )

    def _build_element(self, screenshot_path: str, box, include_ocr: bool, target_text: Optional[str]) -> Dict:
        coords = self._to_coords(box.xyxy)
        label = self._resolve_label(int(box.cls[0]))
        confidence = float(box.conf[0])
        element = {
            "label": label,
            "confidence": confidence,
            "box": coords,
            "center": [(coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2],
            "text": None,
            "is_match": None,
            "strategy": "yolo",
        }

        if include_ocr or target_text:
            patch = crop_element(screenshot_path, coords)
            features = summarize_patch(patch)
            text = features.get("text", "").strip() or None
            is_match = TextSimilarity.is_match(target_text, text or "") if target_text else False
            element.update(
                {
                    "text": text,
                    "is_match": is_match if target_text else None,
                    "strategy": "yolo+opencv+ocr",
                }
            )

        return element


    def detect_ui_elements(
        self,
        screenshot_path: str,
        include_ocr: bool = False,
        target_text: Optional[str] = None,
        min_confidence: float = 0.25,
    ):
        if not self.model.available:
            return []

        results = self.model.predict(screenshot_path, conf=0.1)
        detections = []
        for result in results:
            for box in result.boxes:
                element = self._build_element(screenshot_path, box, include_ocr=include_ocr, target_text=target_text)
                if element["confidence"] >= min_confidence:
                    detections.append(element)
        
        # ---  REFINEMENT  ---
        detections = self.refine_yolo_labels(detections) 
        detections = self._merge_overlapping_elements(detections)
        return self._sort_elements(detections)

    def detect_and_read(self, screenshot_path: str, target_text: str = None, min_confidence: float = 0.25):
        return self.detect_ui_elements(
            screenshot_path=screenshot_path,
            include_ocr=True,
            target_text=target_text,
            min_confidence=min_confidence,
        )
    def _merge_overlapping_elements(self, elements: List[Dict], iou_threshold: float = 0.2) -> List[Dict]:
        if not elements: return []

        # 1. Dima el kbir (high confidence) houwa el "Winner"
        elements = sorted(elements, key=lambda x: x['confidence'], reverse=True)
        keep = []

        while elements:
            current = elements.pop(0)
            keep.append(current)
            
            remaining = []
            for other in elements:
                # 2. Thabbet f'el overlap
                iou = self._calculate_iou(current['box'], other['box'])
                
                if iou > iou_threshold:
                    # --- EL FAZA HNA: DUPLICATION CHECK ---
                    # Ken nafs el label, n-skipiw 'other' khater 'current' khir (Winner takes all)
                    if current['label'] == other['label']:
                        print(f"🚫 Skipping duplicate {other['label']} due to overlap with {current['label']}")
                        continue 
                    
                    # Ken labels tbadlou ama overlaps kbir, n-lemou el text
                    if other['text'] and len(other['text']) > 2:
                        if (other['text'] or "") not in (current['text'] or ""):
                            current['text'] = f"{current['text'] or ''} {other['text']}".strip()
                    
                    # Fel loop mta3 el merging, zid hathi:
                        if iou > 0.2: # Tayya7na l'0.2 bech yelmem kol chy 9rib
                            # Ken current label houwa nafsou other label, n-skipiw el thanti
                            if current['label'] == other['label']:
                                print(f"🚫 Removing duplicate {other['label']} at same location")
                                continue
                else:
                    # Ma fammach overlap? Khalli el element l-ba3d
                    remaining.append(other)
            
            elements = remaining
            
        return keep

    def _calculate_iou(self, boxA, boxB):
        # Logic sghira bech ta7seb el overlap bin 2 boxes
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(boxAArea + boxBArea - interArea)
    
    def refine_yolo_labels(self, detected_elements: List[Dict]) -> List[Dict]:
        """
        Salla7 el labels mta3 YOLO b'esta3mel el dictionary mta3 el Keywords (Multi-lang).
        """
        # Dictionary mte3ek (Polyglot version)
        KEYWORDS = {
                    'input_field': [
                        # French
                        'e-mail', 'numéro', 'mobile', 'password', 'passe', 'username', 'nom', 'prenom', 'recherche', 'écrire', 'saisir',
                        # English
                        'email', 'number', 'phone', 'username', 'last name', 'first name', 'search', 'type here', 'enter', 'address'
                    ],
                    'button': [
                        # French
                        'se connecter', 'login', 'créer', 'compte', 'valider', 'submit', 'cliquer', 'envoyer', 'ok', 'annuler', 'suivant',
                        # English
                        'sign in', 'log in', 'create', 'account', 'validate', 'submit', 'click', 'send', 'next', 'cancel', 'register'
                    ],
                    'dropdown': [
                        # French
                        'choisir', 'sélectionner', 'select', 'pays', 'ville', 'date', 'genre', 'type', 'liste',
                        # English
                        'choose', 'select', 'country', 'city', 'date', 'gender', 'type', 'list', 'option'
                    ],
                    'checkbox': [
                        # French
                        'accepter', 'conditions', 'newsletter', 'se souvenir', 'remember', 'cocher', 'autoriser',
                        # English
                        'accept', 'terms', 'conditions', 'newsletter', 'remember me', 'check', 'allow', 'agree'
                    ],
                    'link': [
                        # French
                        'mot de passe oublié', 'aide', 'contact', 'cliquez ici', 'voir plus', 'en savoir plus', 'ici',
                        # English
                        'forgot password', 'help', 'contact us', 'click here', 'see more', 'read more', 'here'
                    ]
        }

        for el in detected_elements:
            text_lower = el['text'].lower() if el['text'] else ""
            if not text_lower:
                continue

            # N-farksou f'el categories lkol
            for category, keys in KEYWORDS.items():
                if any(kw in text_lower for kw in keys):
                    # Ken l9ina match w el label mta3 YOLO ghalet, n-sal7ouh
                    if el['label'] != category:
                        print(f"🔄 Correcting {el['label']} to '{category}' based on OCR: '{text_lower}'")
                        el['label'] = category
                    # Nal9aw match wa7ed s7i7, n-taddau lel element elli ba3dou
                    break 

        # <--- T-kharajha l-barra mel loop mta3 el ELEMENTS! 
        return detected_elements
