import easyocr
import numpy as np
from PIL import Image
from presidio_image_redactor import TesseractOCR, OCR
import pytesseract
import logging

logger = logging.getLogger(__name__)

class HybridOCR(OCR):
    def __init__(self):
        self.tesseract = TesseractOCR()
        self.easy_reader = None # Lazy load EasyOCR

    def perform_ocr(self, image: object, **kwargs) -> dict:
        ocr_engine = kwargs.get("ocr_engine", "tesseract")
        logger.info(f"Performing OCR using engine: {ocr_engine}")

        if ocr_engine == "easyocr":
            return self._perform_easy_ocr(image)
        else:
            return self.tesseract.perform_ocr(image, **kwargs)

    def _perform_easy_ocr(self, image: object) -> dict:
        try:
            if self.easy_reader is None:
                logger.info("Initializing EasyOCR reader for French...")
                self.easy_reader = easyocr.Reader(['fr'])

            # Convert to numpy array for EasyOCR
            if isinstance(image, Image.Image):
                img_np = np.array(image)
            elif isinstance(image, str):
                img_np = np.array(Image.open(image))
            else:
                img_np = image

            results = self.easy_reader.readtext(img_np)

            # Format EasyOCR results to match Tesseract DICT format
            ocr_dict = {
                "text": [],
                "left": [],
                "top": [],
                "width": [],
                "height": [],
                "conf": []
            }

            for bbox, text, conf in results:
                # bbox is [[x0,y0], [x1,y1], [x2,y2], [x3,y3]]
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                left = min(x_coords)
                top = min(y_coords)
                width = max(x_coords) - left
                height = max(y_coords) - top

                ocr_dict["text"].append(text)
                ocr_dict["left"].append(left)
                ocr_dict["top"].append(top)
                ocr_dict["width"].append(width)
                ocr_dict["height"].append(height)
                ocr_dict["conf"].append(int(conf * 100))

            logger.info(f"EasyOCR complete: extracted {len(ocr_dict['text'])} words")
            return ocr_dict
        except Exception as e:
            logger.error(f"Error during EasyOCR analysis: {e}", exc_info=True)
            # Fallback to Tesseract if EasyOCR fails
            logger.info("Falling back to Tesseract OCR")
            return self.tesseract.perform_ocr(image)
