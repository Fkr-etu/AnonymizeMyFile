import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    @staticmethod
    def process_for_ocr(image_path_or_pil):
        logger.info("Starting image preprocessing for OCR...")
        try:
            # Convert PIL to OpenCV if needed
            if isinstance(image_path_or_pil, Image.Image):
                cv_img = cv2.cvtColor(np.array(image_path_or_pil), cv2.COLOR_RGB2BGR)
            else:
                cv_img = cv2.imread(image_path_or_pil)

            if cv_img is None:
                logger.warning(f"Could not read image for preprocessing: {image_path_or_pil}")
                return image_path_or_pil

            # 1. Grayscale
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            # 2. Denoising
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

            # 3. Thresholding (Binarization)
            # Using adaptive thresholding for varying lighting conditions
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            logger.info("Image preprocessing for OCR complete")
            # Convert back to PIL
            return Image.fromarray(thresh)
        except Exception as e:
            logger.error(f"Error during image preprocessing: {e}", exc_info=True)
            return image_path_or_pil
