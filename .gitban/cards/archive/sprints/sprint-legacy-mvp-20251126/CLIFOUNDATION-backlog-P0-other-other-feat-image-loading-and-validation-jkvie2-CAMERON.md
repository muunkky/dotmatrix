## Description

Implement image loading using OpenCV/Pillow with format validation and error handling.

**Value**: Provides robust image loading that validates formats and provides clear errors, ensuring the detection pipeline receives valid image data.

**Target Users**: Internal module used by CLI

**Estimated Effort**: 1.5 hours

---

## Acceptance Criteria

- [ ] Successfully loads PNG and JPG/JPEG images
- [ ] Returns numpy array in BGR format (OpenCV standard)
- [ ] Rejects unsupported formats with clear error message
- [ ] Handles corrupted images gracefully
- [ ] Validates image has valid dimensions (> 0x0)

---

## Implementation Plan

### Overview

Create an image_loader module that uses cv2.imread with error handling and validation.

### Implementation Steps

1. **Create image_loader.py module**:
   - Define load_image(path: str) -> np.ndarray function
   - Use cv2.imread() for loading
   - Validate result is not None

2. **Implement validation**:
   - Check file extension matches [.png, .jpg, .jpeg]
   - Verify image loaded successfully
   - Check image dimensions are valid
   - Raise descriptive exceptions for each failure mode

3. **Add error handling**:
   - ImageLoadError for file not found
   - ImageFormatError for unsupported format
   - ImageCorruptedError for corrupted files

### Technical Considerations

- **Data Format**: Return BGR numpy array (OpenCV standard)
- **Error Handling**: Custom exception classes for different failure modes

### Dependencies

- **Prerequisites**: Card j5ta2i (project setup) must be complete

---

## Testing Strategy

### Unit Tests

- [ ] Test loading valid PNG image
- [ ] Test loading valid JPG image
- [ ] Test error on missing file
- [ ] Test error on unsupported format (e.g., .bmp, .gif)
- [ ] Test error on corrupted image file
- [ ] Verify output is numpy array with correct shape

---

## Documentation Updates

- [ ] Add docstrings to image_loader module
- [ ] Document supported image formats